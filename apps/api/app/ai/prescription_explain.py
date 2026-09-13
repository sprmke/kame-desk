"""Plain-language explanations for deterministic prescription safety flags."""

from app.ai.clients import openai_configured, run_text_llm, use_stub_provider


def explain_safety_flag_stub(flag: dict[str, str]) -> str:
    flag_type = flag.get("type", "unknown")
    drug = flag.get("drug_name", "this drug")
    related = flag.get("related") or "a listed allergen or interacting drug"
    if flag_type == "allergy":
        return (
            f"{drug} may trigger a reaction linked to {related}. "
            "The chart allergy list matched this prescription."
        )
    if flag_type == "interaction":
        return (
            f"{drug} may interact with {related}. "
            "Review timing, dosing, or choose an alternative if clinically needed."
        )
    return flag.get("message") or "Review this flag against the patient chart."


async def explain_safety_flag(flag: dict[str, str]) -> str:
    if use_stub_provider() or not openai_configured():
        return explain_safety_flag_stub(flag)

    try:
        prompt = (
            "Explain this deterministic safety flag for a doctor: "
            f"type={flag.get('type')}, drug={flag.get('drug_name')}, "
            f"message={flag.get('message')}, related={flag.get('related')}"
        )
        return await run_text_llm(
            (
                "Explain prescription safety flags in plain clinical language. "
                "Do not change severity or recommend overriding the flag."
            ),
            prompt,
        )
    except Exception:
        return explain_safety_flag_stub(flag)
