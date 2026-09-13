import uuid
from datetime import date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ActivityLog, Clinic, ClinicMembership, Patient, User
from app.services.notification_prefs import merged_preferences
from app.services.recall_service import list_clinic_recalls, update_recall_status
from app.services.secrets_crypto import encrypt_json

router = APIRouter(tags=["recalls"])


class ChronicRule(BaseModel):
    condition: str = Field(min_length=1, max_length=128)
    interval_months: int = Field(ge=1, le=36)


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    whatsapp_enabled: bool | None = None
    confirmation_enabled: bool | None = None
    reminder_24h_enabled: bool | None = None
    reminder_2h_enabled: bool | None = None
    sender_name: str | None = Field(default=None, max_length=128)
    chronic_condition_rules: list[ChronicRule] | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_access_token: str | None = None


class NotificationPreferencesRead(BaseModel):
    preferences: dict[str, Any]
    sms_configured: bool
    whatsapp_configured: bool


class RecallRead(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    source: str
    due_date: date
    status: str
    source_soap_note_id: uuid.UUID | None
    created_at: datetime
    patient_name: str | None = None

    model_config = {"from_attributes": True}


class RecallListResponse(BaseModel):
    items: list[RecallRead]
    total: int
    page: int = 1
    page_size: int = 0


class RecallStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|contacted|booked|dismissed)$")


@router.get(
    "/clinics/{clinic_id}/notification-preferences",
    response_model=NotificationPreferencesRead,
)
async def get_notification_preferences(
    clinic_id: uuid.UUID,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPreferencesRead:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    if membership.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Not allowed")
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return NotificationPreferencesRead(
        preferences=merged_preferences(clinic.notification_preferences),
        sms_configured=bool(clinic.twilio_credentials_encrypted),
        whatsapp_configured=bool(clinic.whatsapp_credentials_encrypted),
    )


@router.patch(
    "/clinics/{clinic_id}/notification-preferences",
    response_model=NotificationPreferencesRead,
)
async def patch_notification_preferences(
    clinic_id: uuid.UUID,
    data: NotificationPreferencesUpdate,
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPreferencesRead:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    if membership.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Not allowed")
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not found")

    prefs = merged_preferences(clinic.notification_preferences)
    updates = data.model_dump(
        exclude_unset=True,
        exclude={
            "twilio_account_sid",
            "twilio_auth_token",
            "twilio_from_number",
            "whatsapp_phone_number_id",
            "whatsapp_access_token",
        },
    )
    if updates.get("chronic_condition_rules") is not None:
        updates["chronic_condition_rules"] = [
            r.model_dump() if hasattr(r, "model_dump") else r
            for r in updates["chronic_condition_rules"]
        ]
    prefs.update(updates)

    if data.sms_enabled and not clinic.twilio_credentials_encrypted:
        if not (data.twilio_account_sid and data.twilio_auth_token and data.twilio_from_number):
            raise HTTPException(
                status_code=400,
                detail="Twilio credentials required when SMS is enabled",
            )

    if data.whatsapp_enabled and not clinic.whatsapp_credentials_encrypted:
        if not (data.whatsapp_phone_number_id and data.whatsapp_access_token):
            raise HTTPException(
                status_code=400,
                detail="WhatsApp Business credentials required when WhatsApp is enabled",
            )

    if data.twilio_account_sid and data.twilio_auth_token and data.twilio_from_number:
        clinic.twilio_credentials_encrypted = encrypt_json(
            {
                "account_sid": data.twilio_account_sid,
                "auth_token": data.twilio_auth_token,
                "from_number": data.twilio_from_number,
            }
        )

    if data.whatsapp_phone_number_id and data.whatsapp_access_token:
        existing = await db.execute(
            select(Clinic).where(
                Clinic.whatsapp_phone_number_id == data.whatsapp_phone_number_id,
                Clinic.id != clinic_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=400,
                detail="This WhatsApp phone number ID is already in use by another clinic",
            )
        clinic.whatsapp_phone_number_id = data.whatsapp_phone_number_id
        clinic.whatsapp_credentials_encrypted = encrypt_json(
            {"access_token": data.whatsapp_access_token}
        )

    clinic.notification_preferences = prefs
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=membership.user_id,
            actor_type="user",
            action="clinic.notification_preferences_updated",
            target_type="clinic",
            target_id=str(clinic_id),
            summary="Notification preferences updated",
        )
    )
    await db.commit()
    await db.refresh(clinic)
    return NotificationPreferencesRead(
        preferences=merged_preferences(clinic.notification_preferences),
        sms_configured=bool(clinic.twilio_credentials_encrypted),
        whatsapp_configured=bool(clinic.whatsapp_credentials_encrypted),
    )


@router.get("/clinics/{clinic_id}/recalls", response_model=RecallListResponse)
async def get_recalls(
    clinic_id: uuid.UUID,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = "pending",
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1, le=100),
    sort: str | None = None,
) -> RecallListResponse:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    if membership.role not in ("owner", "admin", "reception"):
        raise HTTPException(status_code=403, detail="Not allowed")
    recalls, total = await list_clinic_recalls(
        db,
        clinic_id,
        status,
        q=q,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    if not recalls:
        return RecallListResponse(
            items=[],
            total=total,
            page=page,
            page_size=page_size or 0,
        )
    patient_ids = {r.patient_id for r in recalls}
    patients = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
    name_map = {p.id: p.full_name for p in patients.scalars().all()}
    items = []
    for r in recalls:
        row = RecallRead.model_validate(r)
        row.patient_name = name_map.get(r.patient_id)
        items.append(row)
    return RecallListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size or total or len(items),
    )


@router.patch("/recalls/{recall_id}", response_model=RecallRead)
async def patch_recall(
    recall_id: uuid.UUID,
    data: RecallStatusUpdate,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecallRead:
    if membership.role not in ("owner", "admin", "reception"):
        raise HTTPException(status_code=403, detail="Not allowed")
    recall = await update_recall_status(db, membership.clinic_id, recall_id, data.status, user.id)
    patient = await db.get(Patient, recall.patient_id)
    row = RecallRead.model_validate(recall)
    row.patient_name = patient.full_name if patient else None
    return row
