import json
import os
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.assistant.orchestrator import ParsedToolCall
from app.ai.assistant.planner import plan_patient_turn
from app.ai.patient_assistant.context import build_grounding_facts
from app.ai.patient_assistant.safety import verify_output_safety
from app.ai.patient_assistant.tools import (
    answer_clinic_faq,
    book_public_appointment,
    check_public_availability,
)
from app.core.rate_limit import enforce_public_rate_limit
from app.models import (
    Clinic,
    ClinicMembership,
    DoctorProfile,
    PatientAssistantConversation,
    PatientAssistantMessage,
    ServiceFee,
    User,
)
from app.schemas.public import PublicAppointmentRequest
from app.services.clinic_service import get_clinic_by_slug


async def _load_grounding(db: AsyncSession, clinic: Clinic) -> dict[str, Any]:
    doctors = await db.execute(
        select(DoctorProfile, User)
        .join(User, User.id == DoctorProfile.user_id)
        .where(DoctorProfile.clinic_id == clinic.id)
    )
    fees = await db.execute(
        select(ServiceFee).where(ServiceFee.clinic_id == clinic.id).order_by(ServiceFee.name)
    )
    return build_grounding_facts(clinic, doctors.all(), list(fees.scalars()))


async def _owner_user_id(db: AsyncSession, clinic_id: uuid.UUID) -> uuid.UUID:
    owner = await db.execute(
        select(User)
        .join(ClinicMembership, ClinicMembership.user_id == User.id)
        .where(
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.role == "owner",
            ClinicMembership.is_active.is_(True),
        )
        .limit(1)
    )
    user = owner.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=503, detail="Clinic is not ready for bookings")
    return user.id


async def _get_or_create_conversation(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
) -> PatientAssistantConversation:
    if conversation_id:
        row = await db.get(PatientAssistantConversation, conversation_id)
        if row is None or row.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return row
    row = PatientAssistantConversation(
        clinic_id=clinic_id,
        created_at=datetime.now(UTC),
    )
    db.add(row)
    await db.flush()
    return row


async def _save_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> PatientAssistantMessage:
    msg = PatientAssistantMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        metadata_=metadata,
        created_at=datetime.now(UTC),
    )
    db.add(msg)
    await db.flush()
    return msg


async def _run_tool(
    db: AsyncSession,
    slug: str,
    clinic: Clinic,
    grounding: dict[str, Any],
    call: ParsedToolCall,
) -> dict[str, Any]:
    if call.name == "check_public_availability":
        doctor_id = uuid.UUID(str(call.args["doctor_id"]))
        on_date = datetime.fromisoformat(str(call.args["date"])).date()
        return await check_public_availability(db, clinic.id, doctor_id, on_date)
    if call.name == "book_public_appointment":
        owner_id = await _owner_user_id(db, clinic.id)
        payload = PublicAppointmentRequest.model_validate(call.args)
        return await book_public_appointment(db, slug, payload, owner_id)
    if call.name == "answer_clinic_faq":
        return answer_clinic_faq(grounding, str(call.args.get("question", "")))
    raise HTTPException(status_code=400, detail=f"Unknown tool: {call.name}")


def _summarize_tool(name: str, result: dict[str, Any]) -> str:
    if name == "check_public_availability":
        return f"{result.get('total', 0)} slots available."
    if name == "book_public_appointment":
        return "Your appointment request was submitted."
    if name == "answer_clinic_faq":
        return str(result.get("answer", ""))
    return f"{name} completed."


def _looks_like_booking(content: str) -> bool:
    lowered = content.lower()
    return any(word in lowered for word in ("book", "appointment", "schedule", "reserve", "slot"))


async def stream_patient_assistant_turn(
    db: AsyncSession,
    slug: str,
    request: Request,
    content: str,
    conversation_id: uuid.UUID | None,
) -> AsyncIterator[str]:
    enforce_public_rate_limit(request, slug)
    clinic = await get_clinic_by_slug(db, slug)
    grounding = await _load_grounding(db, clinic)
    conversation = await _get_or_create_conversation(db, clinic.id, conversation_id)
    await _save_message(db, conversation.id, "user", content)

    yield f"data: {json.dumps({'type': 'conversation_id', 'id': str(conversation.id)})}\n\n"

    allow_explicit = os.environ.get("DOCTORDESK_TESTING") == "1"
    plan = await plan_patient_turn(content, grounding, allow_explicit_tools=allow_explicit)
    tool_results: list[dict[str, Any]] = []
    for call in plan.calls:
        result = await _run_tool(db, slug, clinic, grounding, call)
        tool_results.append({"tool": call.name, "result": result})

    if tool_results:
        reply = " ".join(_summarize_tool(r["tool"], r["result"]) for r in tool_results)
    elif plan.llm_failed:
        reply = (
            "Booking is unavailable right now. Use the booking form, or try again in a moment."
            if _looks_like_booking(content)
            else answer_clinic_faq(grounding, content)["answer"]
        )
    elif plan.reply:
        reply = plan.reply
    else:
        faq = answer_clinic_faq(grounding, content)
        reply = faq["answer"]

    reply = verify_output_safety(reply, grounding)
    await _save_message(
        db,
        conversation.id,
        "assistant",
        reply,
        metadata={"tool_results": tool_results},
    )
    await db.commit()

    yield f"data: {json.dumps({'type': 'text', 'content': reply})}\n\n"
    for result in tool_results:
        yield f"data: {json.dumps({'type': 'tool_result', **result})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
