import logging
from typing import Any

from pydantic import BaseModel, Field

from app.ai.assistant.context import AttachedContextItem, PageContext
from app.ai.assistant.orchestrator import ParsedToolCall, parse_tool_calls
from app.ai.assistant.tools import TOOL_REGISTRY
from app.ai.clients import openai_configured, run_structured_llm, use_stub_provider

logger = logging.getLogger(__name__)

STAFF_TOOL_DESCRIPTIONS: dict[str, str] = {
    "search_patients": "Search patients by name, contact, or number. Args: q (string).",
    "get_patient": "Get one patient. Args: patient_id (uuid).",
    "list_appointments": (
        "List appointments. Optional args: patient_id, doctor_id, status, date (YYYY-MM-DD)."
    ),
    "get_available_slots": "Open slots for a doctor on a date. Args: doctor_id, date (YYYY-MM-DD).",
    "check_patient_balance": "Outstanding balance. Args: patient_id.",
    "search_charts": "Search SOAP notes. Args: q (string). Doctor/owner only.",
    "check_eligibility_status": (
        "Latest HMO/PhilHealth eligibility check on file for a patient (read-only, does not call "
        "the insurer). Args: patient_id."
    ),
    "draft_soap_note": "Draft SOAP fields from input_text. Args: appointment_id, input_text.",
    "revoke_pending_staff_invite": "Revoke an unused staff invite. Args: invitation_id.",
    "advance_appointment_status": (
        "Forward-only appointment status (e.g. Scheduled to Confirmed). Args: appointment_id."
    ),
    "propose_book_appointment": (
        "Propose booking. Args: patient_id, doctor_id, scheduled_start, scheduled_end, "
        "reason_for_visit (optional)."
    ),
    "propose_reschedule_appointment": (
        "Propose reschedule. Args: appointment_id, scheduled_start, scheduled_end."
    ),
    "propose_cancel_appointment": "Propose cancel. Args: appointment_id.",
    "propose_save_soap_note": (
        "Propose SOAP save. Args: appointment_id plus subjective/objective/assessment/plan."
    ),
    "propose_issue_prescription": "Propose Rx draft. Args: patient_id, appointment_id, items[].",
    "propose_create_invoice_line": "Propose invoice line. Args: invoice_id, description, amount.",
    "propose_send_reminder": "Propose sending a reminder. Args: appointment_id.",
    "propose_generate_document": (
        "Propose issuing a letter. Args: patient_id, template_id, appointment_id (optional)."
    ),
}

PATIENT_TOOL_DESCRIPTIONS: dict[str, str] = {
    "check_public_availability": ("List open slots. Args: doctor_id (uuid), date (YYYY-MM-DD)."),
    "book_public_appointment": (
        "Submit a booking request. Args: doctor_id, scheduled_start, scheduled_end, "
        "full_name, contact_number, reason_for_visit (optional)."
    ),
    "answer_clinic_faq": "Answer hours, fees, or contact from clinic facts. Args: question.",
}

STAFF_SYSTEM_PROMPT = """You are the DoctorDesk clinic assistant for authenticated staff.
Return which tools to call, if any. Do not invent IDs, names, balances, or clinical facts.
If a write is needed, use the matching propose_* tool (or advance/revoke). Never claim a write is done.
If you cannot fulfill the request with the listed tools, leave calls empty and explain briefly in reply.
Do not include patient content beyond what the user already typed."""

PATIENT_SYSTEM_PROMPT = """You help a guest book an appointment or answer clinic FAQ.
Use only the listed tools. Do not invent hours, fees, doctors, or availability.
For booking you must have doctor_id plus start and end times; otherwise call check_public_availability first
or ask a short clarifying question in reply with no tools.
Never claim another patient's data. Never give medical advice."""


class ToolCallSpec(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class LlmToolPlan(BaseModel):
    calls: list[ToolCallSpec] = Field(default_factory=list)
    reply: str = ""


class AssistantPlan:
    __slots__ = ("calls", "reply", "llm_failed")

    def __init__(
        self,
        calls: list[ParsedToolCall],
        reply: str = "",
        *,
        llm_failed: bool = False,
    ) -> None:
        self.calls = calls
        self.reply = reply
        self.llm_failed = llm_failed


def _catalog_block(descriptions: dict[str, str], allowed: set[str] | None = None) -> str:
    lines = []
    for name, desc in descriptions.items():
        if allowed is not None and name not in allowed:
            continue
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def _ids_only_context(
    page: PageContext | None,
    attached: list[AttachedContextItem] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if page:
        payload["page"] = {
            "route": page.route,
            "patient_id": str(page.patient_id) if page.patient_id else None,
            "appointment_id": str(page.appointment_id) if page.appointment_id else None,
            "visit_id": str(page.visit_id) if page.visit_id else None,
        }
    if attached:
        payload["attached"] = [{"type": item.type, "id": str(item.id)} for item in attached]
    return payload


def _to_parsed(plan: LlmToolPlan, allowed: set[str]) -> AssistantPlan:
    calls: list[ParsedToolCall] = []
    for spec in plan.calls:
        name = spec.name.strip()
        if name not in allowed:
            continue
        calls.append(ParsedToolCall(name=name, args=spec.args or {}))
    return AssistantPlan(calls=calls, reply=(plan.reply or "").strip())


async def plan_staff_turn(
    content: str,
    page: PageContext | None = None,
    attached: list[AttachedContextItem] | None = None,
) -> AssistantPlan:
    explicit = parse_tool_calls(content)
    if explicit:
        return AssistantPlan(calls=explicit)

    allowed = set(TOOL_REGISTRY)
    if use_stub_provider() or not openai_configured():
        return AssistantPlan(
            calls=[],
            reply="The clinic assistant is not configured. Add an AI API key, or ask again later.",
            llm_failed=not use_stub_provider(),
        )

    user_prompt = (
        "Available tools:\n"
        f"{_catalog_block(STAFF_TOOL_DESCRIPTIONS, allowed)}\n\n"
        f"Screen context (IDs only): {_ids_only_context(page, attached)}\n\n"
        f"Staff message:\n{content}"
    )
    try:
        planned = await run_structured_llm(LlmToolPlan, STAFF_SYSTEM_PROMPT, user_prompt)
    except Exception:
        logger.exception("Staff assistant planner failed")
        return AssistantPlan(
            calls=[],
            reply="The assistant could not reach the AI service. Try again in a moment.",
            llm_failed=True,
        )
    return _to_parsed(planned, allowed)


async def plan_patient_turn(
    content: str,
    grounding: dict[str, Any],
    *,
    allow_explicit_tools: bool,
) -> AssistantPlan:
    if allow_explicit_tools:
        explicit = parse_tool_calls(content)
        if explicit:
            return AssistantPlan(calls=explicit)

    allowed = set(PATIENT_TOOL_DESCRIPTIONS)
    if use_stub_provider() or not openai_configured():
        return AssistantPlan(calls=[], reply="")

    safe_grounding = {
        "clinic_name": grounding.get("clinic_name"),
        "working_hours": grounding.get("working_hours"),
        "contact_phone": grounding.get("contact_phone"),
        "contact_email": grounding.get("contact_email"),
        "services": grounding.get("services"),
        "doctors": grounding.get("doctors"),
    }
    user_prompt = (
        "Available tools:\n"
        f"{_catalog_block(PATIENT_TOOL_DESCRIPTIONS)}\n\n"
        f"Clinic facts: {safe_grounding}\n\n"
        f"Guest message:\n{content}"
    )
    try:
        planned = await run_structured_llm(LlmToolPlan, PATIENT_SYSTEM_PROMPT, user_prompt)
    except Exception:
        logger.exception("Patient assistant planner failed")
        return AssistantPlan(calls=[], reply="", llm_failed=True)
    return _to_parsed(planned, allowed)
