import json
import uuid
from collections.abc import AsyncIterator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.clients import estimate_token_count, stream_soap_draft_fields
from app.ai.schemas import SoapDraftContext
from app.models import ClinicMembership, User
from app.services.ai_usage_service import (
    build_visit_vitals_summary,
    load_chronic_conditions,
    record_ai_usage,
)
from app.services.appointment_service import get_appointment
from app.services.clinical_access import assert_soap_write


async def build_soap_draft_context(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> SoapDraftContext:
    vitals = await build_visit_vitals_summary(db, clinic_id, patient_id)
    chronic = await load_chronic_conditions(db, clinic_id, patient_id)
    return SoapDraftContext(vitals_summary=vitals, chronic_conditions=chronic)


async def stream_soap_draft_sse(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    input_text: str,
    actor: User,
    membership: ClinicMembership,
) -> AsyncIterator[str]:
    appt = await get_appointment(db, clinic_id, appointment_id)
    await assert_soap_write(db, membership, appt.doctor_id, actor)

    context = await build_soap_draft_context(db, clinic_id, appt.patient_id)
    token_estimate = estimate_token_count(input_text, context)

    try:
        async for field, value in stream_soap_draft_fields(input_text, context):
            payload = {"type": "field", "field": field, "value": value}
            yield f"data: {json.dumps(payload)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        await record_ai_usage(db, clinic_id, token_estimate)
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        yield f"data: {json.dumps({'type': 'error', 'message': 'Draft generation failed'})}\n\n"
