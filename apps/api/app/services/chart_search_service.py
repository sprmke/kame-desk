import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_text
from app.core.config import settings
from app.models import ClinicMembership, User
from app.schemas.chart_search import ChartSearchResult
from app.services.clinical_access import get_doctor_profile_for_user


async def search_charts(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    query: str,
    membership: ClinicMembership,
    actor: User,
    limit: int = 20,
) -> list[ChartSearchResult]:
    if membership.role not in ("doctor", "owner"):
        raise PermissionError("Chart search not allowed")

    vector, _model = await embed_text(query.strip())
    vec_literal = "[" + ",".join(str(v) for v in vector) + "]"

    doctor_filter = ""
    params: dict[str, object] = {
        "clinic_id": str(clinic_id),
        "query_vec": vec_literal,
        "limit": limit,
    }

    if membership.role == "doctor":
        doctor = await get_doctor_profile_for_user(db, actor, clinic_id)
        if doctor is None:
            return []
        doctor_filter = "AND sn.doctor_id = :doctor_id"
        params["doctor_id"] = str(doctor.id)

    sql = f"""
        SELECT
            sn.id AS soap_note_id,
            sn.appointment_id,
            sn.patient_id,
            sn.version_number,
            sn.assessment,
            sn.created_at,
            p.full_name AS patient_name,
            1 - (e.embedding <=> CAST(:query_vec AS vector)) AS score
        FROM soap_note_embeddings e
        JOIN soap_notes sn ON sn.id = e.soap_note_id
        JOIN patients p ON p.id = sn.patient_id
        WHERE sn.clinic_id = :clinic_id
        {doctor_filter}
        ORDER BY e.embedding <=> CAST(:query_vec AS vector)
        LIMIT :limit
    """
    result = await db.execute(text(sql), params)
    rows = result.mappings().all()
    out: list[ChartSearchResult] = []
    for row in rows:
        snippet_source = row["assessment"] or ""
        snippet = snippet_source[:240]
        out.append(
            ChartSearchResult(
                soap_note_id=row["soap_note_id"],
                appointment_id=row["appointment_id"],
                patient_id=row["patient_id"],
                patient_name=row["patient_name"],
                version_number=row["version_number"],
                snippet=snippet,
                visit_date=row["created_at"],
                score=float(row["score"] or 0),
            )
        )
    return out


async def purge_expired_recordings(db: AsyncSession) -> int:
    from app.models import ConsultationRecording
    from app.services.storage_service import delete_object

    cutoff = datetime.now(UTC) - timedelta(days=settings.recording_retention_days)
    result = await db.execute(
        select(ConsultationRecording).where(ConsultationRecording.created_at < cutoff)
    )
    rows = list(result.scalars().all())
    deleted = 0
    for row in rows:
        try:
            delete_object(row.r2_key)
        except Exception:
            pass
        await db.delete(row)
        deleted += 1
    if deleted:
        from app.models import ActivityLog

        db.add(
            ActivityLog(
                clinic_id=None,
                actor_user_id=None,
                actor_type="system",
                action="system.cron_run",
                target_type="system",
                target_id="purge_expired_recordings",
                summary="Purged expired consultation recordings",
                metadata_={"count": deleted},
            )
        )
        await db.commit()
    return deleted


async def fail_stale_transcriptions(db: AsyncSession) -> int:
    from app.models import ConsultationRecording

    cutoff = datetime.now(UTC) - timedelta(minutes=settings.transcription_timeout_minutes)
    result = await db.execute(
        select(ConsultationRecording).where(
            ConsultationRecording.transcription_status == "processing",
            ConsultationRecording.processing_started_at < cutoff,
        )
    )
    rows = list(result.scalars().all())
    for row in rows:
        row.transcription_status = "failed"
    if rows:
        await db.commit()
    return len(rows)
