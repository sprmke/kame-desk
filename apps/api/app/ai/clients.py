import logging
import os
from collections.abc import AsyncIterator
from datetime import date, timedelta

from app.ai.prompts.soap_draft import (
    build_soap_draft_system_prompt,
    build_soap_draft_user_prompt,
)
from app.ai.schemas import SoapDraft, SoapDraftContext
from app.core.config import settings

logger = logging.getLogger(__name__)

SOAP_DRAFT_FIELDS = (
    "subjective",
    "objective",
    "assessment",
    "plan",
    "diagnosis_primary",
    "follow_up_date",
)


def use_stub_provider() -> bool:
    if os.environ.get("DOCTORDESK_TESTING") == "1":
        return True
    return not settings.openai_api_key.strip()


def _use_stub_provider() -> bool:
    return use_stub_provider()


def openai_configured() -> bool:
    return bool(settings.openai_api_key.strip())


def build_openai_chat_model():
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    return OpenAIChatModel(
        settings.ai_model,
        provider=OpenAIProvider(api_key=settings.openai_api_key),
    )


async def run_structured_llm[T](
    output_type: type[T],
    system_prompt: str,
    user_prompt: str,
) -> T:
    from pydantic_ai import Agent

    agent = Agent(
        build_openai_chat_model(),
        output_type=output_type,
        system_prompt=system_prompt,
    )
    result = await agent.run(user_prompt)
    return result.output


async def run_text_llm(system_prompt: str, user_prompt: str) -> str:
    from pydantic_ai import Agent

    agent = Agent(
        build_openai_chat_model(),
        system_prompt=system_prompt,
    )
    result = await agent.run(user_prompt)
    return str(result.output).strip()


async def _stub_soap_draft_stream(
    input_text: str,
    context: SoapDraftContext,
) -> AsyncIterator[tuple[str, str]]:
    subjective = f"Patient reports: {input_text.strip()}"
    objective = context.vitals_summary or "Vitals not recorded for this visit."
    assessment = "Clinical assessment based on presenting complaint."
    if context.chronic_conditions:
        assessment += f" Chronic conditions: {', '.join(context.chronic_conditions)}."
    plan = "Review findings with patient. Adjust treatment as clinically indicated."
    follow_up = (date.today() + timedelta(weeks=2)).isoformat()

    chunks = {
        "subjective": subjective,
        "objective": objective,
        "assessment": assessment,
        "plan": plan,
        "diagnosis_primary": context.chronic_conditions[0] if context.chronic_conditions else "",
        "follow_up_date": follow_up,
    }
    for field in SOAP_DRAFT_FIELDS:
        value = chunks.get(field, "")
        if value:
            yield field, value


async def _pydantic_ai_soap_draft_stream(
    input_text: str,
    context: SoapDraftContext,
) -> AsyncIterator[tuple[str, str]]:
    prompt = build_soap_draft_user_prompt(input_text, context)
    draft = await run_structured_llm(
        SoapDraft,
        build_soap_draft_system_prompt(),
        prompt,
    )
    for field in SOAP_DRAFT_FIELDS:
        value = getattr(draft, field, None)
        if value is None:
            continue
        if isinstance(value, date):
            yield field, value.isoformat()
        else:
            yield field, str(value)


async def stream_soap_draft_fields(
    input_text: str,
    context: SoapDraftContext,
) -> AsyncIterator[tuple[str, str]]:
    if use_stub_provider():
        async for item in _stub_soap_draft_stream(input_text, context):
            yield item
        return

    try:
        async for item in _pydantic_ai_soap_draft_stream(input_text, context):
            yield item
    except Exception:
        logger.exception("SOAP draft generation failed")
        raise


def estimate_token_count(input_text: str, context: SoapDraftContext) -> int:
    blob = input_text + (context.vitals_summary or "") + "".join(context.chronic_conditions)
    return max(1, len(blob) // 4)
