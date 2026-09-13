import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.assistant.context import ResolvedContext
from app.ai.assistant.orchestrator import (
    build_resolved_context,
    summarize_tool_result,
    validate_tool_name,
)
from app.ai.assistant.planner import plan_staff_turn
from app.ai.assistant.safety import (
    assert_tool_role,
    collect_grounding_strings,
    ground_assistant_text,
    load_clinic_for_assistant,
    log_tool_call,
)
from app.ai.assistant.tiers import PlannedToolCall, classify_tier
from app.ai.assistant.tools import ToolRuntime, get_tool
from app.models import (
    ActivityLog,
    AiAssistantAction,
    AiAssistantConversation,
    AiAssistantMessage,
    ClinicMembership,
    User,
)
from app.schemas.assistant import AssistantMessageCreate
from app.services.ai_usage_service import assert_ai_usage_available, record_ai_usage
from app.services.appointment_service import has_schedule_overlap


async def create_conversation(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    user: User,
) -> AiAssistantConversation:
    clinic = await load_clinic_for_assistant(db, clinic_id)
    row = AiAssistantConversation(clinic_id=clinic.id, user_id=user.id)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_conversation(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> AiAssistantConversation:
    result = await db.execute(
        select(AiAssistantConversation).where(
            AiAssistantConversation.id == conversation_id,
            AiAssistantConversation.clinic_id == clinic_id,
            AiAssistantConversation.user_id == user_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return row


async def _booking_overlap_risk(
    db: AsyncSession, clinic_id: uuid.UUID, args: dict[str, Any]
) -> bool:
    start_raw = args.get("scheduled_start")
    end_raw = args.get("scheduled_end")
    doctor_raw = args.get("doctor_id")
    if not start_raw or not end_raw or not doctor_raw:
        return False
    try:
        start = datetime.fromisoformat(str(start_raw))
        end = datetime.fromisoformat(str(end_raw))
        doctor_id = uuid.UUID(str(doctor_raw))
    except (TypeError, ValueError):
        return False
    exclude = None
    if args.get("appointment_id"):
        try:
            exclude = uuid.UUID(str(args["appointment_id"]))
        except ValueError:
            exclude = None
    return await has_schedule_overlap(
        db, clinic_id, doctor_id, start, end, exclude_appointment_id=exclude
    )


async def _save_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> AiAssistantMessage:
    msg = AiAssistantMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        metadata_=metadata,
        created_at=datetime.now(UTC),
    )
    db.add(msg)
    await db.flush()
    return msg


async def _execute_tool_calls(
    db: AsyncSession,
    clinic,
    membership: ClinicMembership,
    user: User,
    context: ResolvedContext,
    calls: list,
    assistant_message_id: uuid.UUID,
    conversation_id: uuid.UUID,
    *,
    actor_type: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Returns (tool_results, pending_actions, grounding_strings)."""
    if not calls:
        return [], [], []

    planned = []
    for call in calls:
        validate_tool_name(call.name)
        tool = get_tool(call.name)
        planned.append(
            PlannedToolCall(
                name=call.name,
                args=call.args,
                base_tier=tool.base_tier,
                is_write=tool.is_write,
                is_clinical_write=tool.is_clinical_write,
                is_external_send=tool.is_external_send,
            )
        )

    rt = ToolRuntime(
        clinic=clinic, membership=membership, user=user, context=context, actor_type=actor_type
    )
    tool_results: list[dict[str, Any]] = []
    pending_actions: list[dict[str, Any]] = []
    grounding: list[str] = []

    disabled = set(getattr(clinic, "assistant_disabled_tools", None) or [])

    for call, plan in zip(calls, planned, strict=True):
        tool = get_tool(call.name)
        if call.name in disabled:
            raise HTTPException(status_code=403, detail="This assistant action is disabled")
        assert_tool_role(membership, tool.allowed_roles)
        if plan.name in ("propose_book_appointment", "propose_reschedule_appointment"):
            overlap = await _booking_overlap_risk(db, clinic.id, plan.args)
            if overlap:
                plan.args["overlap_risk"] = True
        tier = classify_tier(plan, planned, context)

        if tier <= 1:
            try:
                proposal_or_result = await tool.handler(db, rt, call.args)
                if tool.is_write and tool.confirm_handler:
                    result = await tool.confirm_handler(db, rt, proposal_or_result)
                else:
                    result = proposal_or_result
            except HTTPException:
                log_tool_call(call.name, tier, "error")
                raise
            log_tool_call(call.name, tier, "executed")
            tool_results.append({"tool": call.name, "tier": tier, "result": result})
            grounding.extend(collect_grounding_strings(result))
            if tool.is_write:
                db.add(
                    ActivityLog(
                        clinic_id=clinic.id,
                        actor_user_id=user.id,
                        actor_type=actor_type,
                        action=f"assistant.tool.{call.name}",
                        target_type="ai_assistant_action",
                        target_id=str(conversation_id),
                        summary=f"AI assistant executed {call.name}",
                        metadata_={"tier": tier, "result": result},
                    )
                )
            continue

        proposal = await tool.handler(db, rt, call.args)
        action = AiAssistantAction(
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            tool_name=call.name,
            tier=tier,
            status="pending",
            proposal=proposal,
            external_send=tool.is_external_send,
            created_at=datetime.now(UTC),
        )
        db.add(action)
        await db.flush()
        log_tool_call(call.name, tier, "proposed")
        pending_actions.append(
            {
                "action_id": str(action.id),
                "tool": call.name,
                "tier": tier,
                "proposal": proposal,
                "external_send": tool.is_external_send,
            }
        )

    return tool_results, pending_actions, grounding


async def stream_assistant_turn(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    data: AssistantMessageCreate,
    membership: ClinicMembership,
    user: User,
) -> AsyncIterator[str]:
    clinic = await load_clinic_for_assistant(db, membership.clinic_id)
    conversation = await get_conversation(db, clinic.id, user.id, conversation_id)
    await assert_ai_usage_available(db, clinic.id)

    await _save_message(db, conversation.id, "user", data.content)
    context = build_resolved_context(data.page_context, data.attached_context)
    plan = await plan_staff_turn(data.content, data.page_context, data.attached_context)
    calls = plan.calls

    assistant_msg = await _save_message(
        db, conversation.id, "assistant", "", metadata={"tools": []}
    )
    if plan.llm_failed and not calls:
        reply = plan.reply or "The assistant could not reach the AI service. Try again in a moment."
        assistant_msg.content = reply
        assistant_msg.metadata_ = {"llm_failed": True}
        await db.commit()
        yield f"data: {json.dumps({'type': 'error', 'message': reply})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    try:
        tool_results, pending_actions, grounding = await _execute_tool_calls(
            db,
            clinic,
            membership,
            user,
            context,
            calls,
            assistant_msg.id,
            conversation.id,
            actor_type="ai_assistant",
        )
    except HTTPException as exc:
        await db.rollback()
        payload = {"type": "error", "message": exc.detail}
        yield f"data: {json.dumps(payload)}\n\n"
        return

    summary_parts = [summarize_tool_result(r["tool"], r["result"]) for r in tool_results]
    if pending_actions:
        summary_parts.append(f"{len(pending_actions)} action(s) need confirmation.")
    fallback = plan.reply or "How can I help?"
    reply = ground_assistant_text(" ".join(summary_parts) if summary_parts else fallback, grounding)

    assistant_msg.content = reply
    assistant_msg.metadata_ = {"tool_results": tool_results, "pending_actions": pending_actions}
    await db.commit()

    yield f"data: {json.dumps({'type': 'text', 'content': reply})}\n\n"
    for result in tool_results:
        yield f"data: {json.dumps({'type': 'tool_result', **result})}\n\n"
    for action in pending_actions:
        yield f"data: {json.dumps({'type': 'confirm_card', **action})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
    await record_ai_usage(db, clinic.id)


async def confirm_action(
    db: AsyncSession,
    action_id: uuid.UUID,
    membership: ClinicMembership,
    user: User,
) -> dict[str, Any]:
    clinic = await load_clinic_for_assistant(db, membership.clinic_id)
    result = await db.execute(
        select(AiAssistantAction)
        .join(AiAssistantConversation)
        .where(
            AiAssistantAction.id == action_id,
            AiAssistantConversation.clinic_id == clinic.id,
            AiAssistantConversation.user_id == user.id,
        )
    )
    action = result.scalar_one_or_none()
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status != "pending":
        raise HTTPException(status_code=400, detail="Action is not pending")

    tool = get_tool(action.tool_name)
    assert_tool_role(membership, tool.allowed_roles)
    if tool.confirm_handler is None:
        raise HTTPException(status_code=400, detail="Action cannot be confirmed")

    await get_conversation(db, clinic.id, user.id, action.conversation_id)
    rt = ToolRuntime(
        clinic=clinic,
        membership=membership,
        user=user,
        context=ResolvedContext(),
        actor_type="ai_assistant",
    )

    if tool.pre_confirm_check:
        await tool.pre_confirm_check(db, rt, action.proposal)

    try:
        outcome = await tool.confirm_handler(db, rt, action.proposal)
    except HTTPException:
        log_tool_call(action.tool_name, action.tier, "confirm_failed")
        raise

    action.status = "confirmed"
    action.result = outcome
    action.executed_at = datetime.now(UTC)
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=user.id,
            actor_type="ai_assistant",
            action=f"assistant.tool.{action.tool_name}",
            target_type="ai_assistant_action",
            target_id=str(action.id),
            summary=f"AI assistant confirmed {action.tool_name}",
            metadata_={"tier": action.tier, "result": outcome},
        )
    )
    await db.commit()
    log_tool_call(action.tool_name, action.tier, "confirmed")
    return {"action_id": str(action.id), "status": "confirmed", "result": outcome}


async def cancel_action(
    db: AsyncSession,
    action_id: uuid.UUID,
    membership: ClinicMembership,
    user: User,
) -> dict[str, Any]:
    clinic = await load_clinic_for_assistant(db, membership.clinic_id)
    result = await db.execute(
        select(AiAssistantAction)
        .join(AiAssistantConversation)
        .where(
            AiAssistantAction.id == action_id,
            AiAssistantConversation.clinic_id == clinic.id,
            AiAssistantConversation.user_id == user.id,
        )
    )
    action = result.scalar_one_or_none()
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status != "pending":
        raise HTTPException(status_code=400, detail="Action is not pending")
    action.status = "cancelled"
    await db.commit()
    log_tool_call(action.tool_name, action.tier, "cancelled")
    return {"action_id": str(action.id), "status": "cancelled"}
