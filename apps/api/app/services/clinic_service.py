import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    ActivityLog,
    Clinic,
    ClinicMembership,
    DoctorProfile,
    Room,
    ServiceFee,
    StaffInvitation,
    User,
)
from app.schemas.clinic import (
    BirComplianceRead,
    BirComplianceUpdate,
    ClinicRead,
    ClinicUpdate,
    DoctorProfileCreate,
    DoctorProfileUpdate,
    GrowthSettingsRead,
    GrowthSettingsUpdate,
    InvitationAccept,
    InvitationCreate,
    OnboardingStatusRead,
    OnboardingStepStatus,
    ReceiptNumberingRead,
    ReceiptNumberingUpdate,
    RoomCreate,
    RoomUpdate,
    ServiceFeeCreate,
    ServiceFeeUpdate,
    WorkingHoursUpdate,
)
from app.services.email_service import send_invitation_email
from app.services.invoice_service import DEFAULT_NUMBERING


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


async def get_clinic(db: AsyncSession, clinic_id: uuid.UUID) -> Clinic:
    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    clinic = result.scalar_one_or_none()
    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")
    return clinic


def numbering_read(clinic: Clinic) -> ReceiptNumberingRead:
    merged = {**DEFAULT_NUMBERING, **(clinic.receipt_numbering_config or {})}
    return ReceiptNumberingRead(
        prefix=str(merged.get("prefix", "OR-")),
        next_number=int(merged.get("next_number", 1)),
        pad_width=int(merged.get("pad_width", 6)),
    )


def _resolve_logo_url(logo_url: str | None) -> str | None:
    if not logo_url:
        return None
    if logo_url.startswith("clinics/"):
        from app.services.storage_service import create_presigned_download

        return create_presigned_download(logo_url)
    return logo_url


def to_clinic_read(clinic: Clinic) -> ClinicRead:
    row = ClinicRead.model_validate(clinic)
    row.logo_url = _resolve_logo_url(clinic.logo_url)
    row.receipt_numbering = numbering_read(clinic)
    row.bir_compliance = bir_compliance_read(clinic)
    row.growth_settings = growth_settings_read(clinic)
    return row


async def enrich_clinic_read(db: AsyncSession, clinic: Clinic) -> ClinicRead:
    row = to_clinic_read(clinic)
    if clinic.organization_id is not None:
        from app.services.organization_service import get_org_subscription, resolve_plan_key

        sub = await get_org_subscription(db, clinic.organization_id)
        row.plan_key = resolve_plan_key(sub, clinic)
    return row


async def update_receipt_numbering(
    db: AsyncSession, clinic: Clinic, data: ReceiptNumberingUpdate, actor_id: uuid.UUID
) -> Clinic:
    clinic.receipt_numbering_config = {
        "prefix": data.prefix,
        "next_number": data.next_number,
        "pad_width": data.pad_width,
    }
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type="user",
            action="clinic.receipt_numbering_updated",
            target_type="clinic",
            target_id=str(clinic.id),
            summary="Receipt numbering updated",
        )
    )
    await db.commit()
    await db.refresh(clinic)
    return clinic


def bir_compliance_read(clinic: Clinic) -> BirComplianceRead:
    config = clinic.bir_compliance_config or {}
    return BirComplianceRead(
        tin=config.get("tin"),
        registered_name=config.get("registered_name"),
        registered_address=config.get("registered_address"),
        vat_registered=bool(config.get("vat_registered", False)),
        compliance_mode=config.get("compliance_mode", "not_yet_accredited"),
        accreditation_number=config.get("accreditation_number"),
        accreditation_valid_until=config.get("accreditation_valid_until"),
    )


async def update_bir_compliance(
    db: AsyncSession, clinic: Clinic, data: BirComplianceUpdate, actor_id: uuid.UUID
) -> Clinic:
    clinic.bir_compliance_config = data.model_dump()
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type="user",
            action="clinic.bir_compliance_updated",
            target_type="clinic",
            target_id=str(clinic.id),
            summary="BIR compliance settings updated",
        )
    )
    await db.commit()
    await db.refresh(clinic)
    return clinic


def preview_bir_compliance_pdf(clinic: Clinic, data: BirComplianceUpdate) -> bytes:
    from app.models import Invoice, InvoiceLineItem, Patient
    from app.services.invoice_pdf import render_invoice_pdf

    preview_clinic = Clinic(
        id=clinic.id,
        name=clinic.name,
        address=clinic.address,
        brand_color=clinic.brand_color,
        bir_compliance_config=data.model_dump(),
    )
    patient = Patient(id=uuid.uuid4(), full_name="Juan Dela Cruz")
    invoice = Invoice(
        id=uuid.uuid4(),
        invoice_number="OR-000001",
        subtotal=Decimal("1120.00"),
        total=Decimal("1120.00"),
        issued_at=datetime.now(UTC),
    )
    invoice.line_items = [
        InvoiceLineItem(
            id=uuid.uuid4(),
            description="Consultation (sample)",
            amount=Decimal("1120.00"),
            unit_price=Decimal("1120.00"),
        )
    ]
    invoice.payments = []
    return render_invoice_pdf(preview_clinic, patient, invoice)


def growth_settings_read(clinic: Clinic) -> GrowthSettingsRead:
    config = clinic.growth_settings or {}
    return GrowthSettingsRead(
        google_review_link=config.get("google_review_link"),
        review_requests_enabled=bool(config.get("review_requests_enabled", False)),
        doh_accreditation_number=config.get("doh_accreditation_number"),
        doh_accreditation_valid_until=config.get("doh_accreditation_valid_until"),
    )


async def update_growth_settings(
    db: AsyncSession, clinic: Clinic, data: GrowthSettingsUpdate, actor_id: uuid.UUID
) -> Clinic:
    clinic.growth_settings = data.model_dump()
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type="user",
            action="clinic.growth_settings_updated",
            target_type="clinic",
            target_id=str(clinic.id),
            summary="Growth & retention settings updated",
        )
    )
    await db.commit()
    await db.refresh(clinic)
    return clinic


async def get_clinic_by_slug(db: AsyncSession, slug: str) -> Clinic:
    result = await db.execute(select(Clinic).where(Clinic.slug == slug))
    clinic = result.scalar_one_or_none()
    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")
    return clinic


async def update_clinic(
    db: AsyncSession, clinic: Clinic, data: ClinicUpdate, actor_id: uuid.UUID
) -> Clinic:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(clinic, field, value)
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type="user",
            action="clinic.updated",
            target_type="clinic",
            target_id=str(clinic.id),
            summary="Clinic profile updated",
        )
    )
    await _maybe_complete_onboarding(db, clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


async def update_working_hours(
    db: AsyncSession,
    clinic: Clinic,
    data: WorkingHoursUpdate,
    actor_id: uuid.UUID,
) -> Clinic:
    clinic.working_hours = {k: v.model_dump() for k, v in data.working_hours.items()}
    clinic.holiday_dates = data.holiday_dates
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type="user",
            action="clinic.working_hours_updated",
            target_type="clinic",
            target_id=str(clinic.id),
            summary="Working hours updated",
        )
    )
    await _maybe_complete_onboarding(db, clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


async def skip_invite_step(db: AsyncSession, clinic: Clinic, actor_id: uuid.UUID) -> Clinic:
    clinic.onboarding_invite_skipped = True
    await _maybe_complete_onboarding(db, clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


async def compute_onboarding_status(db: AsyncSession, clinic: Clinic) -> OnboardingStatusRead:
    owner_profile = await _owner_doctor_profile(db, clinic.id)
    fees_count = await db.scalar(
        select(func.count()).select_from(ServiceFee).where(ServiceFee.clinic_id == clinic.id)
    )

    clinic_done = bool(
        clinic.address and clinic.contact_phone and clinic.contact_email and clinic.license_info
    )
    doctor_done = bool(
        owner_profile
        and owner_profile.specialty
        and owner_profile.prc_license_number
        and owner_profile.consultation_fee is not None
    )
    hours_done = bool(clinic.working_hours and len(clinic.working_hours) > 0)
    fees_done = bool(
        (owner_profile and owner_profile.consultation_fee is not None)
        or (fees_count and fees_count > 0)
    )
    invite_done = clinic.onboarding_invite_skipped
    if not invite_done:
        pending_invites = await db.scalar(
            select(func.count())
            .select_from(StaffInvitation)
            .where(StaffInvitation.clinic_id == clinic.id)
        )
        invite_done = bool(pending_invites and pending_invites > 0)

    steps = [
        OnboardingStepStatus(key="clinic", label="Clinic profile", complete=clinic_done),
        OnboardingStepStatus(key="doctor", label="Doctor profile", complete=doctor_done),
        OnboardingStepStatus(key="hours", label="Working hours", complete=hours_done),
        OnboardingStepStatus(key="fees", label="Fees", complete=fees_done),
        OnboardingStepStatus(key="invite", label="Invite staff", complete=invite_done),
    ]
    required_complete = all(s.complete for s in steps[:4]) and invite_done
    current = next((s.key for s in steps if not s.complete), None)
    return OnboardingStatusRead(steps=steps, all_complete=required_complete, current_step=current)


async def _maybe_complete_onboarding(db: AsyncSession, clinic: Clinic) -> None:
    status = await compute_onboarding_status(db, clinic)
    if status.all_complete and clinic.onboarding_completed_at is None:
        clinic.onboarding_completed_at = datetime.now(UTC)


async def _owner_doctor_profile(db: AsyncSession, clinic_id: uuid.UUID) -> DoctorProfile | None:
    result = await db.execute(
        select(DoctorProfile)
        .join(ClinicMembership, ClinicMembership.user_id == DoctorProfile.user_id)
        .where(
            DoctorProfile.clinic_id == clinic_id,
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.role == "owner",
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_or_update_doctor_profile(
    db: AsyncSession,
    clinic: Clinic,
    data: DoctorProfileCreate,
    actor_id: uuid.UUID,
) -> DoctorProfile:
    user_id = data.user_id
    if user_id is None:
        if not data.email:
            raise HTTPException(status_code=400, detail="user_id or email required")
        user_result = await db.execute(select(User).where(User.email == data.email.lower()))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=400, detail="User not found; send an invitation first")
        user_id = user.id

    mem = await db.execute(
        select(ClinicMembership).where(
            ClinicMembership.clinic_id == clinic.id,
            ClinicMembership.user_id == user_id,
            ClinicMembership.is_active.is_(True),
        )
    )
    membership = mem.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=400, detail="User is not an active clinic member")
    if membership.role not in ("owner", "doctor", "admin"):
        membership.role = "doctor"

    existing = await db.execute(
        select(DoctorProfile).where(
            DoctorProfile.clinic_id == clinic.id, DoctorProfile.user_id == user_id
        )
    )
    profile = existing.scalar_one_or_none()
    if profile is None:
        profile = DoctorProfile(
            user_id=user_id,
            clinic_id=clinic.id,
            specialty=data.specialty,
            prc_license_number=data.prc_license_number,
            consultation_fee=data.consultation_fee,
            follow_up_fee=data.follow_up_fee,
            default_appointment_duration_minutes=data.default_appointment_duration_minutes,
        )
        db.add(profile)
    else:
        profile.specialty = data.specialty
        profile.prc_license_number = data.prc_license_number
        profile.consultation_fee = data.consultation_fee
        profile.follow_up_fee = data.follow_up_fee
        profile.default_appointment_duration_minutes = data.default_appointment_duration_minutes

    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type="user",
            action="doctor_profile.upserted",
            target_type="doctor_profile",
            target_id=str(profile.id),
            summary="Doctor profile saved",
        )
    )
    await _maybe_complete_onboarding(db, clinic)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_doctor_profile(
    db: AsyncSession,
    profile: DoctorProfile,
    data: DoctorProfileUpdate,
    actor_id: uuid.UUID,
) -> DoctorProfile:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.add(
        ActivityLog(
            clinic_id=profile.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="doctor_profile.updated",
            target_type="doctor_profile",
            target_id=str(profile.id),
            summary="Doctor profile updated",
        )
    )
    clinic = await get_clinic(db, profile.clinic_id)
    await _maybe_complete_onboarding(db, clinic)
    await db.commit()
    await db.refresh(profile)
    return profile


async def list_service_fees(db: AsyncSession, clinic_id: uuid.UUID) -> list[ServiceFee]:
    result = await db.execute(select(ServiceFee).where(ServiceFee.clinic_id == clinic_id))
    return list(result.scalars().all())


async def create_service_fee(
    db: AsyncSession, clinic_id: uuid.UUID, data: ServiceFeeCreate, actor_id: uuid.UUID
) -> ServiceFee:
    fee = ServiceFee(clinic_id=clinic_id, **data.model_dump())
    db.add(fee)
    await db.flush()
    clinic = await get_clinic(db, clinic_id)
    await _maybe_complete_onboarding(db, clinic)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="service_fee.created",
            target_type="service_fee",
            target_id=str(fee.id),
            summary=f"Service fee added: {fee.name}",
        )
    )
    await db.commit()
    await db.refresh(fee)
    return fee


async def update_service_fee(
    db: AsyncSession, fee: ServiceFee, data: ServiceFeeUpdate, actor_id: uuid.UUID
) -> ServiceFee:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fee, field, value)
    db.add(
        ActivityLog(
            clinic_id=fee.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="service_fee.updated",
            target_type="service_fee",
            target_id=str(fee.id),
            summary=f"Service fee updated: {fee.name}",
        )
    )
    await db.commit()
    await db.refresh(fee)
    return fee


async def delete_service_fee(db: AsyncSession, fee: ServiceFee, actor_id: uuid.UUID) -> None:
    db.add(
        ActivityLog(
            clinic_id=fee.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="service_fee.deleted",
            target_type="service_fee",
            target_id=str(fee.id),
            summary=f"Service fee removed: {fee.name}",
        )
    )
    await db.delete(fee)
    await db.commit()


async def list_rooms(db: AsyncSession, clinic_id: uuid.UUID) -> list[Room]:
    result = await db.execute(select(Room).where(Room.clinic_id == clinic_id).order_by(Room.name))
    return list(result.scalars().all())


async def create_room(
    db: AsyncSession, clinic_id: uuid.UUID, data: RoomCreate, actor_id: uuid.UUID
) -> Room:
    room = Room(clinic_id=clinic_id, name=data.name.strip(), is_active=True)
    db.add(room)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="room.created",
            target_type="room",
            target_id=str(room.id),
            summary="Consult room added",
        )
    )
    await db.commit()
    await db.refresh(room)
    return room


async def update_room(db: AsyncSession, room: Room, data: RoomUpdate, actor_id: uuid.UUID) -> Room:
    payload = data.model_dump(exclude_unset=True)
    if "name" in payload and payload["name"]:
        room.name = payload["name"].strip()
    if "is_active" in payload and payload["is_active"] is not None:
        room.is_active = payload["is_active"]
    db.add(
        ActivityLog(
            clinic_id=room.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="room.updated",
            target_type="room",
            target_id=str(room.id),
            summary="Consult room updated",
        )
    )
    await db.commit()
    await db.refresh(room)
    return room


async def create_invitation(
    db: AsyncSession,
    clinic: Clinic,
    data: InvitationCreate,
    actor_id: uuid.UUID,
) -> tuple[StaffInvitation, str]:
    if data.role == "doctor":
        from app.services.seat_service import assert_doctor_seat_available

        await assert_doctor_seat_available(db, clinic)

    email = data.email.lower()
    existing_member = await db.execute(
        select(ClinicMembership)
        .join(User, User.id == ClinicMembership.user_id)
        .where(ClinicMembership.clinic_id == clinic.id, User.email == email)
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already a clinic member")

    raw_token = _generate_token()
    metadata = None
    if data.doctor_profile:
        metadata = data.doctor_profile.model_dump(mode="json")

    invitation = StaffInvitation(
        clinic_id=clinic.id,
        email=email,
        role=data.role,
        invited_by_user_id=actor_id,
        token_hash=_hash_token(raw_token),
        metadata_=metadata,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(invitation)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_id,
            actor_type="user",
            action="staff_invitation.created",
            target_type="staff_invitation",
            target_id=str(invitation.id),
            summary=f"Invited {email} as {data.role}",
        )
    )
    await db.commit()
    await db.refresh(invitation)

    accept_url = f"{settings.web_base_url}/invitations/accept?token={raw_token}"
    send_invitation_email(email, accept_url, clinic.name)
    return invitation, raw_token


async def resend_invitation(
    db: AsyncSession, invitation: StaffInvitation, clinic: Clinic, actor_id: uuid.UUID
) -> StaffInvitation:
    if invitation.accepted_at or invitation.revoked_at:
        raise HTTPException(status_code=400, detail="Invitation cannot be resent")
    raw_token = _generate_token()
    invitation.token_hash = _hash_token(raw_token)
    invitation.expires_at = datetime.now(UTC) + timedelta(days=7)
    db.add(
        ActivityLog(
            clinic_id=invitation.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="staff.invitation_resent",
            target_type="staff_invitation",
            target_id=str(invitation.id),
            summary=f"Invitation resent to {invitation.email}",
        )
    )
    await db.commit()
    await db.refresh(invitation)
    accept_url = f"{settings.web_base_url}/invitations/accept?token={raw_token}"
    send_invitation_email(invitation.email, accept_url, clinic.name)
    return invitation


async def revoke_invitation(
    db: AsyncSession, invitation: StaffInvitation, actor_id: uuid.UUID, *, actor_type: str = "user"
) -> None:
    if invitation.accepted_at or invitation.revoked_at:
        raise HTTPException(status_code=400, detail="Invitation cannot be revoked")
    invitation.revoked_at = datetime.now(UTC)
    db.add(
        ActivityLog(
            clinic_id=invitation.clinic_id,
            actor_user_id=actor_id,
            actor_type=actor_type,
            action="staff.invitation_revoked",
            target_type="staff_invitation",
            target_id=str(invitation.id),
            summary=f"Invitation revoked for {invitation.email}",
        )
    )
    await db.commit()


async def accept_invitation(
    db: AsyncSession, raw_token: str, data: InvitationAccept
) -> ClinicMembership:
    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(StaffInvitation).where(StaffInvitation.token_hash == token_hash)
    )
    invitation = result.scalar_one_or_none()
    if invitation is None or invitation.revoked_at or invitation.accepted_at:
        raise HTTPException(status_code=400, detail="Invalid invitation")
    if invitation.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invitation expired")

    user_result = await db.execute(select(User).where(User.email == invitation.email))
    user = user_result.scalar_one_or_none()
    if user is None:
        if not data.password or not data.full_name:
            raise HTTPException(status_code=400, detail="Account details required")
        user = User(
            email=invitation.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        db.add(user)
        await db.flush()

    existing = await db.execute(
        select(ClinicMembership).where(
            ClinicMembership.clinic_id == invitation.clinic_id,
            ClinicMembership.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already a clinic member")

    clinic = await db.get(Clinic, invitation.clinic_id)
    if clinic is not None and invitation.role == "doctor":
        from app.services.seat_service import assert_doctor_seat_available

        await assert_doctor_seat_available(db, clinic, exclude_invitation_id=invitation.id)

    membership = ClinicMembership(
        user_id=user.id,
        clinic_id=invitation.clinic_id,
        role=invitation.role,
        is_active=True,
    )
    db.add(membership)
    invitation.accepted_at = datetime.now(UTC)
    await db.flush()

    if invitation.metadata_ and invitation.role == "doctor":
        meta = invitation.metadata_
        db.add(
            DoctorProfile(
                user_id=user.id,
                clinic_id=invitation.clinic_id,
                specialty=meta.get("specialty"),
                prc_license_number=meta.get("prc_license_number"),
                consultation_fee=Decimal(str(meta.get("consultation_fee", 0))),
                follow_up_fee=(
                    Decimal(str(meta["follow_up_fee"])) if meta.get("follow_up_fee") else None
                ),
            )
        )

    db.add(
        ActivityLog(
            clinic_id=invitation.clinic_id,
            actor_user_id=user.id,
            actor_type="user",
            action="staff_invitation.accepted",
            target_type="clinic_membership",
            target_id=str(membership.id),
            summary=f"{user.email} joined as {invitation.role}",
        )
    )
    await db.commit()
    await db.refresh(membership)
    from app.services.notification_service import notify_staff_joined

    await notify_staff_joined(
        db,
        clinic_id=invitation.clinic_id,
        user_id=user.id,
        full_name=user.full_name,
    )
    return membership


async def list_members(db: AsyncSession, clinic_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(ClinicMembership, User)
        .join(User, User.id == ClinicMembership.user_id)
        .where(ClinicMembership.clinic_id == clinic_id)
    )
    rows = []
    for m, u in result.all():
        rows.append(
            {
                "id": m.id,
                "user_id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": m.role,
                "is_active": m.is_active,
            }
        )
    return rows


async def update_membership(
    db: AsyncSession,
    membership: ClinicMembership,
    role: str | None,
    is_active: bool | None,
    actor_id: uuid.UUID,
) -> ClinicMembership:
    if is_active is False and membership.user_id == actor_id and membership.role == "owner":
        raise HTTPException(
            status_code=400,
            detail="Transfer ownership before deactivating your account",
        )
    if role == "owner" or membership.role == "owner":
        owners = await db.scalar(
            select(func.count())
            .select_from(ClinicMembership)
            .where(
                ClinicMembership.clinic_id == membership.clinic_id,
                ClinicMembership.role == "owner",
                ClinicMembership.is_active.is_(True),
            )
        )
        if membership.role == "owner" and role and role != "owner" and owners <= 1:
            raise HTTPException(status_code=400, detail="Clinic must have at least one owner")
        if is_active is False and membership.role == "owner" and owners <= 1:
            raise HTTPException(status_code=400, detail="Cannot deactivate the last owner")

    old_role = membership.role
    if role is not None:
        membership.role = role
    if is_active is not None:
        membership.is_active = is_active

    db.add(
        ActivityLog(
            clinic_id=membership.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="clinic_membership.updated",
            target_type="clinic_membership",
            target_id=str(membership.id),
            summary="Team member updated",
        )
    )
    await db.commit()
    await db.refresh(membership)
    if role is not None and role != old_role:
        from app.services.notification_service import notify_membership_role_changed

        await notify_membership_role_changed(
            db,
            clinic_id=membership.clinic_id,
            membership_id=membership.id,
            user_id=membership.user_id,
            new_role=membership.role,
            actor_user_id=actor_id,
        )
    return membership
