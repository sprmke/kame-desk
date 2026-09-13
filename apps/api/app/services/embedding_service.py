import uuid
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_text, soap_note_embedding_text
from app.models import SoapNote
from app.models.base import new_uuid


async def upsert_soap_note_embedding(db: AsyncSession, soap_note_id: uuid.UUID) -> bool:
    result = await db.execute(select(SoapNote).where(SoapNote.id == soap_note_id))
    note = result.scalar_one_or_none()
    if note is None:
        return False

    body = soap_note_embedding_text(
        note.subjective,
        note.objective,
        note.assessment,
        note.plan,
        note.diagnosis_primary,
    )
    vector, model_version = await embed_text(body)
    vec_literal = "[" + ",".join(str(v) for v in vector) + "]"

    await db.execute(
        text(
            """
            INSERT INTO soap_note_embeddings (
                id, soap_note_id, clinic_id, embedding, embedding_model_version, created_at
            )
            VALUES (
                :id, :soap_note_id, :clinic_id, CAST(:vec AS vector), :model_version, :created_at
            )
            ON CONFLICT (soap_note_id) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                embedding_model_version = EXCLUDED.embedding_model_version
            """
        ),
        {
            "id": str(new_uuid()),
            "soap_note_id": str(soap_note_id),
            "clinic_id": str(note.clinic_id),
            "vec": vec_literal,
            "model_version": model_version,
            "created_at": datetime.now(UTC),
        },
    )
    await db.commit()
    return True
