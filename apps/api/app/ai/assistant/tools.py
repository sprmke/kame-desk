import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from datetime import date as date_cls
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.assistant.context import ResolvedContext, resolve_tool_args
from app.ai.assistant.safety import assert_tool_role
from app.ai.clients import stream_soap_draft_fields
from app.ai.soap_draft_service import build_soap_draft_context
from app.models import Clinic, ClinicMembership, StaffInvitation, User
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.schemas.billing import InvoiceLineItemCreate
from app.schemas.document import GeneratedDocumentCreate
from app.schemas.prescription import PrescriptionCreate, PrescriptionItemCreate
from app.schemas.soap import SoapNoteCreate
from app.services import slot_service
from app.services.appointment_service import (
    create_appointment,
    get_appointment,
    has_schedule_overlap,
    list_appointments,
    reschedule_appointment,
    update_appointment,
)
from app.services.chart_search_service import search_charts
from app.services.clinic_service import get_clinic, revoke_invitation
from app.services.document_service import create_document_draft, issue_document
from app.services.invoice_service import add_line_item, get_invoice, get_patient_balance
from app.services.patient_service import get_patient, list_patients
from app.services.prescription_safety import check_allergy_interaction_conflicts
from app.services.prescription_service import create_prescription_draft
from app.services.reminder_service import schedule_appointment_reminders, send_single_reminder
from app.services.soap_service import create_soap_version

ToolHandler = Callable[[AsyncSession, "ToolRuntime", dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass
class ToolRuntime:
    clinic: Clinic
    membership: ClinicMembership
    user: User
    context: ResolvedContext
    actor_type: str = "user"


@dataclass
class ToolDefinition:
    name: str
    base_tier: int
    is_write: bool
    allowed_roles: tuple[str, ...]
    handler: ToolHandler
    is_clinical_write: bool = False
    is_external_send: bool = False
    confirm_handler: ToolHandler | None = None
    pre_confirm_check: (
        Callable[[AsyncSession, ToolRuntime, dict[str, Any]], Awaitable[None]] | None
    ) = None


def _uuid(value: Any, field: str) -> uuid.UUID:
    if value is None:
        raise HTTPException(status_code=400, detail=f"{field} required")
    return uuid.UUID(str(value))


async def _handle_search_patients(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    assert_tool_role(rt.membership, ("owner", "admin", "doctor", "reception"))
    merged = resolve_tool_args(args, rt.context)
    items, total = await list_patients(
        db,
        rt.clinic.id,
        merged.get("q"),
        int(merged.get("page", 1)),
        int(merged.get("page_size", 10)),
    )
    return {
        "items": [
            {
                "id": str(p.id),
                "full_name": p.full_name,
                "patient_number": p.patient_number,
                "contact_number": p.contact_number,
            }
            for p in items
        ],
        "total": total,
    }


async def _handle_get_patient(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    merged = resolve_tool_args(args, rt.context)
    patient = await get_patient(db, rt.clinic.id, _uuid(merged.get("patient_id"), "patient_id"))
    return {
        "id": str(patient.id),
        "full_name": patient.full_name,
        "patient_number": patient.patient_number,
        "contact_number": patient.contact_number,
        "email": patient.email,
    }


async def _handle_list_appointments(
    db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]
) -> dict:
    merged = resolve_tool_args(args, rt.context)
    patient_id = merged.get("patient_id")
    items, total = await list_appointments(
        db,
        rt.clinic.id,
        doctor_id=_uuid(merged["doctor_id"], "doctor_id") if merged.get("doctor_id") else None,
        patient_id=_uuid(patient_id, "patient_id") if patient_id else None,
        status_filter=merged.get("status"),
        start_from=datetime.fromisoformat(merged["start_from"])
        if merged.get("start_from")
        else None,
        start_to=datetime.fromisoformat(merged["start_to"]) if merged.get("start_to") else None,
    )
    return {
        "items": [
            {
                "id": str(a.id),
                "patient_id": str(a.patient_id),
                "appointment_status": a.appointment_status,
                "scheduled_start": a.scheduled_start.isoformat(),
            }
            for a in items[:20]
        ],
        "total": total,
    }


async def _handle_get_available_slots(
    db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]
) -> dict:
    merged = resolve_tool_args(args, rt.context)
    raw_date = merged.get("date")
    if raw_date is None:
        raise HTTPException(status_code=400, detail="date required")
    on_date = date_cls.fromisoformat(raw_date) if isinstance(raw_date, str) else raw_date
    slots = await slot_service.get_available_slots(
        db,
        rt.clinic,
        _uuid(merged["doctor_id"], "doctor_id"),
        on_date,
        int(merged.get("duration_minutes", rt.clinic.default_appointment_duration_minutes)),
    )
    return {"slots": slots}


async def _handle_check_balance(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    from app.services.billing_access import assert_billing_read

    assert_billing_read(rt.membership)
    merged = resolve_tool_args(args, rt.context)
    balance, count = await get_patient_balance(
        db, rt.clinic.id, _uuid(merged.get("patient_id"), "patient_id")
    )
    return {"balance": str(balance), "open_invoice_count": count}


async def _handle_check_eligibility_status(
    db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]
) -> dict:
    from app.services.billing_access import assert_billing_read
    from app.services.eligibility_service import list_eligibility_checks

    assert_billing_read(rt.membership)
    merged = resolve_tool_args(args, rt.context)
    checks, _ = await list_eligibility_checks(
        db, rt.clinic.id, rt.membership, patient_id=_uuid(merged.get("patient_id"), "patient_id")
    )
    latest = checks[0] if checks else None
    if latest is None:
        return {"found": False}
    return {
        "found": True,
        "payer_name": latest.payer_name,
        "payer_type": latest.payer_type,
        "status": latest.status,
        "verified_amount": str(latest.verified_amount) if latest.verified_amount else None,
        "checked_at": latest.checked_at.isoformat(),
    }


async def _handle_search_charts(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    q = str(args.get("q", "")).strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query required")
    try:
        items = await search_charts(db, rt.clinic.id, q, rt.membership, rt.user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {
        "items": [
            {
                "soap_note_id": str(i.soap_note_id),
                "appointment_id": str(i.appointment_id),
                "patient_id": str(i.patient_id),
                "snippet": i.snippet,
                "score": i.score,
            }
            for i in items
        ]
    }


async def _handle_draft_soap(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    from app.services.clinical_access import assert_soap_write

    merged = resolve_tool_args(args, rt.context)
    appointment_id = _uuid(merged.get("appointment_id"), "appointment_id")
    appt = await get_appointment(db, rt.clinic.id, appointment_id)
    await assert_soap_write(db, rt.membership, appt.doctor_id, rt.user)
    input_text = str(merged.get("input_text", "")).strip()
    if not input_text:
        raise HTTPException(status_code=400, detail="input_text required")
    context = await build_soap_draft_context(db, rt.clinic.id, appt.patient_id)
    draft: dict[str, str] = {}
    async for field, value in stream_soap_draft_fields(input_text, context):
        draft[field] = value
    return {"appointment_id": str(appointment_id), "draft": draft}


async def _handle_revoke_invite(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    assert_tool_role(rt.membership, ("owner", "admin"))
    invitation_id = _uuid(args.get("invitation_id"), "invitation_id")
    result = await db.execute(
        select(StaffInvitation).where(
            StaffInvitation.id == invitation_id,
            StaffInvitation.clinic_id == rt.clinic.id,
        )
    )
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    await revoke_invitation(db, invitation, rt.user.id, actor_type=rt.actor_type)
    return {"invitation_id": str(invitation_id), "status": "revoked"}


async def _handle_advance_status(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    merged = resolve_tool_args(args, rt.context)
    appointment_id = _uuid(merged.get("appointment_id"), "appointment_id")
    appt = await get_appointment(db, rt.clinic.id, appointment_id)
    if appt.appointment_status != "Scheduled":
        raise HTTPException(status_code=400, detail="Only Scheduled appointments can be confirmed")
    updated = await update_appointment(
        db,
        rt.clinic,
        appt,
        AppointmentUpdate(appointment_status="Confirmed"),
        rt.user.id,
        actor_type=rt.actor_type,
    )
    return {"appointment_id": str(updated.id), "appointment_status": updated.appointment_status}


async def _propose_book(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    merged = resolve_tool_args(args, rt.context)
    start_raw = merged.get("scheduled_start")
    end_raw = merged.get("scheduled_end")
    doctor_id = _uuid(merged.get("doctor_id"), "doctor_id")
    overlap = False
    if start_raw and end_raw:
        start = datetime.fromisoformat(str(start_raw))
        end = datetime.fromisoformat(str(end_raw))
        overlap = await has_schedule_overlap(db, rt.clinic.id, doctor_id, start, end)
    return {
        "patient_id": str(_uuid(merged.get("patient_id"), "patient_id")),
        "doctor_id": str(doctor_id),
        "scheduled_start": start_raw,
        "scheduled_end": end_raw,
        "reason_for_visit": merged.get("reason_for_visit"),
        "overlap_risk": overlap,
    }


async def _confirm_book(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    data = AppointmentCreate(
        patient_id=_uuid(args["patient_id"], "patient_id"),
        doctor_id=_uuid(args["doctor_id"], "doctor_id"),
        scheduled_start=datetime.fromisoformat(args["scheduled_start"]),
        scheduled_end=datetime.fromisoformat(args["scheduled_end"]),
        reason_for_visit=args.get("reason_for_visit"),
    )
    appt = await create_appointment(
        db,
        rt.clinic,
        data,
        rt.user.id,
        booking_source="ai_assistant",
        actor_type=rt.actor_type,
    )
    return {"appointment_id": str(appt.id), "appointment_status": appt.appointment_status}


async def _propose_reschedule(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    merged = resolve_tool_args(args, rt.context)
    appt_id = _uuid(merged.get("appointment_id"), "appointment_id")
    appt = await get_appointment(db, rt.clinic.id, appt_id)
    start_raw = merged.get("scheduled_start")
    end_raw = merged.get("scheduled_end")
    overlap = False
    if start_raw and end_raw:
        start = datetime.fromisoformat(str(start_raw))
        end = datetime.fromisoformat(str(end_raw))
        overlap = await has_schedule_overlap(
            db,
            rt.clinic.id,
            appt.doctor_id,
            start,
            end,
            exclude_appointment_id=appt.id,
        )
    return {
        "appointment_id": str(appt.id),
        "scheduled_start": start_raw,
        "scheduled_end": end_raw,
        "overlap_risk": overlap,
    }


async def _confirm_reschedule(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    appt = await get_appointment(db, rt.clinic.id, _uuid(args["appointment_id"], "appointment_id"))
    updated = await reschedule_appointment(
        db,
        rt.clinic,
        appt,
        datetime.fromisoformat(args["scheduled_start"]),
        datetime.fromisoformat(args["scheduled_end"]),
        rt.user.id,
        actor_type=rt.actor_type,
    )
    return {
        "appointment_id": str(updated.id),
        "scheduled_start": updated.scheduled_start.isoformat(),
    }


async def _propose_cancel(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    merged = resolve_tool_args(args, rt.context)
    appt = await get_appointment(
        db, rt.clinic.id, _uuid(merged.get("appointment_id"), "appointment_id")
    )
    return {
        "appointment_id": str(appt.id),
        "appointment_status": appt.appointment_status,
        "scheduled_start": appt.scheduled_start.isoformat(),
    }


async def _confirm_cancel(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    appt = await get_appointment(db, rt.clinic.id, _uuid(args["appointment_id"], "appointment_id"))
    if appt.appointment_status in ("Cancelled", "No Show", "Rescheduled"):
        raise HTTPException(status_code=409, detail="Appointment already terminal")
    updated = await update_appointment(
        db,
        rt.clinic,
        appt,
        AppointmentUpdate(appointment_status="Cancelled"),
        rt.user.id,
        actor_type=rt.actor_type,
    )
    return {"appointment_id": str(updated.id), "appointment_status": updated.appointment_status}


async def _propose_save_soap(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    merged = resolve_tool_args(args, rt.context)
    return {
        "appointment_id": str(_uuid(merged.get("appointment_id"), "appointment_id")),
        "note": merged.get("note") or {},
    }


async def _confirm_save_soap(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    note_data = args.get("note") or {}
    data = SoapNoteCreate.model_validate(note_data)
    note = await create_soap_version(
        db,
        rt.clinic.id,
        _uuid(args["appointment_id"], "appointment_id"),
        data,
        rt.user,
        rt.membership,
        actor_type=rt.actor_type,
    )
    return {"appointment_id": str(note.appointment_id), "version_number": note.version_number}


async def _propose_rx(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    merged = resolve_tool_args(args, rt.context)
    patient_id = _uuid(merged.get("patient_id"), "patient_id")
    items = merged.get("items") or []
    drug_names = [str(i.get("drug_name", "")) for i in items if i.get("drug_name")]
    conflicts = await check_allergy_interaction_conflicts(db, patient_id, drug_names)
    return {
        "patient_id": str(patient_id),
        "appointment_id": merged.get("appointment_id"),
        "items": items,
        "safety_flags": conflicts,
    }


async def _confirm_rx(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    items = [PrescriptionItemCreate.model_validate(i) for i in args.get("items") or []]
    data = PrescriptionCreate(
        appointment_id=_uuid(args["appointment_id"], "appointment_id")
        if args.get("appointment_id")
        else None,
        items=items,
        notes=args.get("notes"),
    )
    rx = await create_prescription_draft(
        db,
        rt.clinic.id,
        _uuid(args["patient_id"], "patient_id"),
        data,
        rt.user,
        rt.membership,
        actor_type=rt.actor_type,
    )
    return {"prescription_id": str(rx.id), "status": rx.status}


async def _propose_invoice_line(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    merged = resolve_tool_args(args, rt.context)
    invoice_id = _uuid(merged.get("invoice_id"), "invoice_id")
    invoice = await get_invoice(db, rt.clinic.id, invoice_id)
    return {
        "invoice_id": str(invoice.id),
        "description": merged.get("description"),
        "quantity": merged.get("quantity", 1),
        "unit_price": merged.get("unit_price"),
        "category": merged.get("category"),
    }


async def _confirm_invoice_line(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    data = InvoiceLineItemCreate(
        description=str(args.get("description")),
        quantity=Decimal(str(args.get("quantity", 1))),
        unit_price=Decimal(str(args.get("unit_price"))),
        category=args.get("category"),
    )
    invoice = await add_line_item(
        db,
        rt.clinic.id,
        _uuid(args["invoice_id"], "invoice_id"),
        data,
        rt.user,
        rt.membership,
        actor_type=rt.actor_type,
    )
    return {"invoice_id": str(invoice.id), "line_count": len(invoice.line_items)}


async def _propose_send_reminder(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    merged = resolve_tool_args(args, rt.context)
    appt = await get_appointment(
        db, rt.clinic.id, _uuid(merged.get("appointment_id"), "appointment_id")
    )
    patient = await get_patient(db, rt.clinic.id, appt.patient_id)
    return {
        "appointment_id": str(appt.id),
        "patient_name": patient.full_name,
        "scheduled_start": appt.scheduled_start.isoformat(),
        "channel": merged.get("channel", "email"),
    }


async def _confirm_send_reminder(db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]) -> dict:
    appt = await get_appointment(db, rt.clinic.id, _uuid(args["appointment_id"], "appointment_id"))
    patient = await get_patient(db, rt.clinic.id, appt.patient_id)
    clinic = await get_clinic(db, rt.clinic.id)
    rows = await schedule_appointment_reminders(
        db, appt, clinic, patient, include_types=("confirmation",)
    )
    if not rows:
        raise HTTPException(status_code=400, detail="No reminder channel available")
    reminder = rows[0]
    reminder.scheduled_send_at = datetime.now(UTC)
    await send_single_reminder(db, reminder, clinic, appt, patient)
    await db.commit()
    return {"reminder_id": str(reminder.id), "status": reminder.status}


async def _propose_generate_document(
    db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]
) -> dict:
    merged = resolve_tool_args(args, rt.context)
    return {
        "patient_id": str(_uuid(merged.get("patient_id"), "patient_id")),
        "template_id": str(_uuid(merged.get("template_id"), "template_id")),
        "appointment_id": merged.get("appointment_id"),
    }


async def _confirm_generate_document(
    db: AsyncSession, rt: ToolRuntime, args: dict[str, Any]
) -> dict:
    data = GeneratedDocumentCreate(
        template_id=_uuid(args["template_id"], "template_id"),
        appointment_id=_uuid(args["appointment_id"], "appointment_id")
        if args.get("appointment_id")
        else None,
    )
    doc = await create_document_draft(
        db,
        rt.clinic.id,
        _uuid(args["patient_id"], "patient_id"),
        data,
        rt.user,
        rt.membership,
        actor_type=rt.actor_type,
    )
    issued = await issue_document(
        db, rt.clinic.id, doc.id, rt.user, rt.membership, actor_type=rt.actor_type
    )
    return {"document_id": str(issued.id), "status": issued.status}


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "search_patients": ToolDefinition(
        "search_patients",
        0,
        False,
        ("owner", "admin", "doctor", "reception"),
        _handle_search_patients,
    ),
    "get_patient": ToolDefinition(
        "get_patient", 0, False, ("owner", "admin", "doctor", "reception"), _handle_get_patient
    ),
    "list_appointments": ToolDefinition(
        "list_appointments",
        0,
        False,
        ("owner", "admin", "doctor", "reception"),
        _handle_list_appointments,
    ),
    "get_available_slots": ToolDefinition(
        "get_available_slots",
        0,
        False,
        ("owner", "admin", "doctor", "reception"),
        _handle_get_available_slots,
    ),
    "check_patient_balance": ToolDefinition(
        "check_patient_balance",
        0,
        False,
        ("owner", "admin", "doctor", "reception"),
        _handle_check_balance,
    ),
    "search_charts": ToolDefinition(
        "search_charts", 0, False, ("owner", "doctor"), _handle_search_charts
    ),
    "check_eligibility_status": ToolDefinition(
        "check_eligibility_status",
        0,
        False,
        ("owner", "admin", "doctor", "reception"),
        _handle_check_eligibility_status,
    ),
    "draft_soap_note": ToolDefinition(
        "draft_soap_note",
        0,
        False,
        ("owner", "doctor"),
        _handle_draft_soap,
        is_clinical_write=False,
    ),
    "revoke_pending_staff_invite": ToolDefinition(
        "revoke_pending_staff_invite", 1, True, ("owner", "admin"), _handle_revoke_invite
    ),
    "advance_appointment_status": ToolDefinition(
        "advance_appointment_status",
        1,
        True,
        ("owner", "admin", "reception"),
        _handle_advance_status,
    ),
    "propose_book_appointment": ToolDefinition(
        "propose_book_appointment",
        1,
        True,
        ("owner", "admin", "reception"),
        _propose_book,
        confirm_handler=_confirm_book,
    ),
    "propose_reschedule_appointment": ToolDefinition(
        "propose_reschedule_appointment",
        1,
        True,
        ("owner", "admin", "reception"),
        _propose_reschedule,
        confirm_handler=_confirm_reschedule,
    ),
    "propose_cancel_appointment": ToolDefinition(
        "propose_cancel_appointment",
        2,
        True,
        ("owner", "admin", "reception"),
        _propose_cancel,
        confirm_handler=_confirm_cancel,
        is_clinical_write=False,
    ),
    "propose_save_soap_note": ToolDefinition(
        "propose_save_soap_note",
        2,
        True,
        ("owner", "doctor"),
        _propose_save_soap,
        confirm_handler=_confirm_save_soap,
        is_clinical_write=True,
    ),
    "propose_issue_prescription": ToolDefinition(
        "propose_issue_prescription",
        2,
        True,
        ("owner", "doctor"),
        _propose_rx,
        confirm_handler=_confirm_rx,
        is_clinical_write=True,
    ),
    "propose_create_invoice_line": ToolDefinition(
        "propose_create_invoice_line",
        2,
        True,
        ("owner", "admin", "reception"),
        _propose_invoice_line,
        confirm_handler=_confirm_invoice_line,
    ),
    "propose_send_reminder": ToolDefinition(
        "propose_send_reminder",
        2,
        True,
        ("owner", "admin", "reception"),
        _propose_send_reminder,
        confirm_handler=_confirm_send_reminder,
        is_external_send=True,
    ),
    "propose_generate_document": ToolDefinition(
        "propose_generate_document",
        2,
        True,
        ("owner", "admin", "doctor"),
        _propose_generate_document,
        confirm_handler=_confirm_generate_document,
        is_clinical_write=True,
    ),
}


def get_tool(name: str) -> ToolDefinition:
    tool = TOOL_REGISTRY.get(name)
    if tool is None:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {name}")
    return tool
