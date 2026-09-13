from app.ai.schemas import SoapDraftContext


def build_soap_draft_system_prompt() -> str:
    return (
        "You are a clinical documentation assistant for a small outpatient clinic. "
        "Expand the doctor's short note into a structured SOAP draft. "
        "Use concise, professional language. Do not invent vitals or conditions "
        "that are not provided in context. Mark uncertainty when data is missing."
    )


def build_soap_draft_user_prompt(input_text: str, context: SoapDraftContext) -> str:
    lines = [f"Doctor note:\n{input_text.strip()}"]
    if context.vitals_summary:
        lines.append(f"Current visit vitals:\n{context.vitals_summary}")
    if context.chronic_conditions:
        joined = ", ".join(context.chronic_conditions)
        lines.append(f"Known chronic conditions:\n{joined}")
    lines.append("Return a complete SOAP draft with assessment and plan.")
    return "\n\n".join(lines)
