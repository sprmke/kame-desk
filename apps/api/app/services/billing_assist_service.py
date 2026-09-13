import base64
import os
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.billing_extract import extract_billing_fields_from_text
from app.models import ActivityLog, BillingExtractionAttempt, User
from app.services.ai_usage_service import assert_ai_usage_available, record_ai_usage
from app.services.billing_access import assert_billing_write
from app.services.patient_service import get_patient
from app.services.storage_service import upload_object_bytes

ALLOWED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "text/plain",
}
MAX_BYTES = 10_000_000


async def _ocr_image_text(content: bytes, content_type: str) -> str:
    if os.environ.get("DOCTORDESK_TESTING") == "1":
        return ""
    try:
        from openai import AsyncOpenAI

        from app.core.config import settings

        if not settings.openai_api_key.strip():
            return ""
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        encoded = base64.standard_b64encode(content).decode()
        response = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract all visible text from this receipt or invoice image. "
                                "Return plain text only."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{content_type};base64,{encoded}"},
                        },
                    ],
                }
            ],
            max_tokens=1200,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception:
        return ""


async def _text_from_upload(content: bytes, content_type: str) -> str:
    if content_type == "text/plain":
        return content.decode("utf-8", errors="ignore")
    if content_type == "application/pdf":
        try:
            from io import BytesIO

            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""
    if content_type.startswith("image/"):
        return await _ocr_image_text(content, content_type)
    return ""


async def extract_billing_document(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    raw: bytes,
    content_type: str,
    filename: str,
    actor: User,
    membership,
) -> dict:
    assert_billing_write(membership)
    await get_patient(db, clinic_id, patient_id)
    await assert_ai_usage_available(db, clinic_id)

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if not raw or len(raw) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Invalid file size")

    attempt_id = uuid.uuid4()
    object_key = f"clinics/{clinic_id}/patients/{patient_id}/billing-assist/{attempt_id}/{filename}"
    upload_object_bytes(object_key, raw, content_type)

    text = await _text_from_upload(raw, content_type)
    if not text.strip() and content_type.startswith("image/"):
        text = ""
    extracted = extract_billing_fields_from_text(text)

    row = BillingExtractionAttempt(
        id=attempt_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        actor_user_id=actor.id,
        source_file_r2_key=object_key,
        extracted_data=extracted,
        confirmed=False,
        created_at=datetime.now(UTC),
    )
    db.add(row)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="billing.extraction_attempted",
            target_type="patient",
            target_id=str(patient_id),
            summary="Billing document extraction attempted",
            metadata_={"attempt_id": str(attempt_id)},
        )
    )
    await db.commit()
    await record_ai_usage(db, clinic_id)

    preview_url = None
    try:
        from app.services.storage_service import create_presigned_download

        preview_url = create_presigned_download(object_key)
    except Exception:
        preview_url = None

    return {
        "attempt_id": str(attempt_id),
        "fields": extracted,
        "source_preview_url": preview_url,
    }


async def mark_extraction_confirmed(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    attempt_id: uuid.UUID,
    actor: User,
    membership,
) -> None:
    assert_billing_write(membership)
    row = await db.get(BillingExtractionAttempt, attempt_id)
    if row is None or row.clinic_id != clinic_id or row.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Extraction attempt not found")
    row.confirmed = True
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="billing.extraction_confirmed",
            target_type="patient",
            target_id=str(patient_id),
            summary="Billing extraction draft confirmed",
            metadata_={"attempt_id": str(attempt_id)},
        )
    )
    await db.commit()
