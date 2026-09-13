import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff, OwnerAdmin, OwnerOnly, clinic_from_path
from app.core.security import get_current_user
from app.models import ActivityLog, Clinic, DoctorProfile, Room, ServiceFee, StaffInvitation, User
from app.schemas.clinic import (
    BirComplianceRead,
    BirComplianceUpdate,
    ClinicRead,
    ClinicUpdate,
    DoctorProfileCreate,
    DoctorProfileRead,
    GrowthSettingsRead,
    GrowthSettingsUpdate,
    InvitationCreate,
    InvitationRead,
    MembershipRead,
    MembershipUpdate,
    OnboardingStatusRead,
    PresignedUploadRequest,
    PresignedUploadResponse,
    ReceiptNumberingRead,
    ReceiptNumberingUpdate,
    RoomCreate,
    RoomRead,
    RoomUpdate,
    SeatSummaryRead,
    ServiceFeeCreate,
    ServiceFeeRead,
    ServiceFeeUpdate,
    WorkingHoursUpdate,
)
from app.schemas.organization import TransferOwnershipRequest
from app.services import clinic_export_service, clinic_service
from app.services.storage_service import create_clinic_logo_upload

router = APIRouter(prefix="/clinics", tags=["clinics"])


@router.get("/{clinic_id}", response_model=ClinicRead)
async def get_clinic_detail(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicRead:
    return await clinic_service.enrich_clinic_read(db, clinic)


@router.post(
    "/{clinic_id}/logo-upload",
    response_model=PresignedUploadResponse,
)
async def logo_upload(
    data: PresignedUploadRequest,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PresignedUploadResponse:
    try:
        url, key = create_clinic_logo_upload(clinic.id, data.content_type, data.file_size_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    clinic.logo_url = key
    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=user.id,
            actor_type="user",
            action="clinic.updated",
            target_type="clinic",
            target_id=str(clinic.id),
            summary="Clinic logo updated",
        )
    )
    await db.commit()
    return PresignedUploadResponse(upload_url=url, object_key=key)


@router.patch("/{clinic_id}", response_model=ClinicRead)
async def patch_clinic(
    data: ClinicUpdate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicRead:
    updated = await clinic_service.update_clinic(db, clinic, data, user.id)
    return clinic_service.to_clinic_read(updated)


@router.put("/{clinic_id}/working-hours", response_model=ClinicRead)
async def put_working_hours(
    data: WorkingHoursUpdate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicRead:
    updated = await clinic_service.update_working_hours(db, clinic, data, user.id)
    return clinic_service.to_clinic_read(updated)


@router.get("/{clinic_id}/onboarding-status", response_model=OnboardingStatusRead)
async def get_onboarding_status(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OnboardingStatusRead:
    return await clinic_service.compute_onboarding_status(db, clinic)


@router.post("/{clinic_id}/onboarding/skip-invite", response_model=ClinicRead)
async def skip_invite(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicRead:
    updated = await clinic_service.skip_invite_step(db, clinic, user.id)
    return clinic_service.to_clinic_read(updated)


@router.get("/{clinic_id}/receipt-numbering", response_model=ReceiptNumberingRead)
async def get_receipt_numbering(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
) -> ReceiptNumberingRead:
    return clinic_service.numbering_read(clinic)


@router.put("/{clinic_id}/receipt-numbering", response_model=ReceiptNumberingRead)
async def put_receipt_numbering(
    data: ReceiptNumberingUpdate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReceiptNumberingRead:
    updated = await clinic_service.update_receipt_numbering(db, clinic, data, user.id)
    return clinic_service.numbering_read(updated)


@router.get("/{clinic_id}/bir-compliance", response_model=BirComplianceRead)
async def get_bir_compliance(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
) -> BirComplianceRead:
    return clinic_service.bir_compliance_read(clinic)


@router.put("/{clinic_id}/bir-compliance", response_model=BirComplianceRead)
async def put_bir_compliance(
    data: BirComplianceUpdate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BirComplianceRead:
    updated = await clinic_service.update_bir_compliance(db, clinic, data, user.id)
    return clinic_service.bir_compliance_read(updated)


@router.post("/{clinic_id}/bir-compliance/preview")
async def preview_bir_compliance(
    data: BirComplianceUpdate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
) -> Response:
    pdf_bytes = clinic_service.preview_bir_compliance_pdf(clinic, data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="receipt-preview.pdf"'},
    )


@router.get("/{clinic_id}/growth-settings", response_model=GrowthSettingsRead)
async def get_growth_settings(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
) -> GrowthSettingsRead:
    return clinic_service.growth_settings_read(clinic)


@router.put("/{clinic_id}/growth-settings", response_model=GrowthSettingsRead)
async def put_growth_settings(
    data: GrowthSettingsUpdate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GrowthSettingsRead:
    updated = await clinic_service.update_growth_settings(db, clinic, data, user.id)
    return clinic_service.growth_settings_read(updated)


@router.get("/{clinic_id}/doctors", response_model=list[DoctorProfileRead])
async def list_doctors(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DoctorProfileRead]:
    result = await db.execute(
        select(DoctorProfile, User)
        .join(User, User.id == DoctorProfile.user_id)
        .where(DoctorProfile.clinic_id == clinic.id)
    )
    out = []
    for profile, user in result.all():
        item = DoctorProfileRead.model_validate(profile)
        item.full_name = user.full_name
        item.email = user.email
        out.append(item)
    return out


@router.post("/{clinic_id}/doctors", response_model=DoctorProfileRead)
async def create_doctor(
    data: DoctorProfileCreate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorProfileRead:
    if data.user_id is None:
        data.user_id = user.id
    profile = await clinic_service.create_or_update_doctor_profile(db, clinic, data, user.id)
    u = await db.get(User, profile.user_id)
    item = DoctorProfileRead.model_validate(profile)
    item.full_name = u.full_name if u else None
    item.email = u.email if u else None
    return item


@router.get("/{clinic_id}/service-fees", response_model=list[ServiceFeeRead])
async def list_fees(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ServiceFeeRead]:
    fees = await clinic_service.list_service_fees(db, clinic.id)
    return [ServiceFeeRead.model_validate(f) for f in fees]


@router.post("/{clinic_id}/service-fees", response_model=ServiceFeeRead)
async def create_fee(
    data: ServiceFeeCreate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceFeeRead:
    fee = await clinic_service.create_service_fee(db, clinic.id, data, user.id)
    return ServiceFeeRead.model_validate(fee)


@router.patch("/{clinic_id}/service-fees/{fee_id}", response_model=ServiceFeeRead)
async def patch_fee(
    fee_id: uuid.UUID,
    data: ServiceFeeUpdate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceFeeRead:
    fee = await db.get(ServiceFee, fee_id)
    if fee is None or fee.clinic_id != clinic.id:
        raise HTTPException(status_code=404, detail="Fee not found")
    fee = await clinic_service.update_service_fee(db, fee, data, user.id)
    return ServiceFeeRead.model_validate(fee)


@router.delete("/{clinic_id}/service-fees/{fee_id}", status_code=204)
async def delete_fee(
    fee_id: uuid.UUID,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    fee = await db.get(ServiceFee, fee_id)
    if fee is None or fee.clinic_id != clinic.id:
        raise HTTPException(status_code=404, detail="Fee not found")
    await clinic_service.delete_service_fee(db, fee, user.id)


@router.get("/{clinic_id}/rooms", response_model=list[RoomRead])
async def list_rooms(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RoomRead]:
    rooms = await clinic_service.list_rooms(db, clinic.id)
    return [RoomRead.model_validate(r) for r in rooms]


@router.post("/{clinic_id}/rooms", response_model=RoomRead)
async def create_room(
    data: RoomCreate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoomRead:
    room = await clinic_service.create_room(db, clinic.id, data, user.id)
    return RoomRead.model_validate(room)


@router.patch("/{clinic_id}/rooms/{room_id}", response_model=RoomRead)
async def patch_room(
    room_id: uuid.UUID,
    data: RoomUpdate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoomRead:
    room = await db.get(Room, room_id)
    if room is None or room.clinic_id != clinic.id:
        raise HTTPException(status_code=404, detail="Room not found")
    updated = await clinic_service.update_room(db, room, data, user.id)
    return RoomRead.model_validate(updated)


@router.get("/{clinic_id}/invitations", response_model=list[InvitationRead])
async def list_invitations(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[InvitationRead]:
    result = await db.execute(select(StaffInvitation).where(StaffInvitation.clinic_id == clinic.id))
    return [InvitationRead.model_validate(i) for i in result.scalars()]


@router.post("/{clinic_id}/invitations", response_model=InvitationRead)
async def create_invitation(
    data: InvitationCreate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvitationRead:
    invitation, _ = await clinic_service.create_invitation(db, clinic, data, user.id)
    return InvitationRead.model_validate(invitation)


@router.delete("/{clinic_id}/invitations/{invitation_id}", status_code=204)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    invitation = await db.get(StaffInvitation, invitation_id)
    if invitation is None or invitation.clinic_id != clinic.id:
        raise HTTPException(status_code=404, detail="Invitation not found")
    await clinic_service.revoke_invitation(db, invitation, user.id)


@router.post("/{clinic_id}/invitations/{invitation_id}/resend", response_model=InvitationRead)
async def resend_invitation(
    invitation_id: uuid.UUID,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvitationRead:
    invitation = await db.get(StaffInvitation, invitation_id)
    if invitation is None or invitation.clinic_id != clinic.id:
        raise HTTPException(status_code=404, detail="Invitation not found")
    updated = await clinic_service.resend_invitation(db, invitation, clinic, user.id)
    return InvitationRead.model_validate(updated)


@router.get("/{clinic_id}/export/patients")
async def export_patients(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    csv_body = await clinic_export_service.export_patients_csv(db, clinic.id, user.id)
    return Response(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="patients.csv"'},
    )


@router.get("/{clinic_id}/export/appointments")
async def export_appointments(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    csv_body = await clinic_export_service.export_appointments_csv(db, clinic.id, user.id)
    return Response(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="appointments.csv"'},
    )


@router.post("/{clinic_id}/deletion-request", response_model=ClinicRead)
async def request_clinic_deletion(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerOnly,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicRead:
    updated = await clinic_export_service.request_clinic_deletion(db, clinic, user, membership)
    return clinic_service.to_clinic_read(updated)


@router.get("/{clinic_id}/seat-summary", response_model=SeatSummaryRead)
async def seat_summary(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SeatSummaryRead:
    from app.services.seat_service import seat_summary as compute_seat_summary

    data = await compute_seat_summary(db, clinic)
    return SeatSummaryRead(**data)


@router.get("/{clinic_id}/members", response_model=list[MembershipRead])
async def list_members(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: OwnerAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MembershipRead]:
    rows = await clinic_service.list_members(db, clinic.id)
    return [MembershipRead.model_validate(r) for r in rows]


@router.post("/{clinic_id}/transfer-ownership", response_model=MembershipRead)
async def transfer_ownership(
    data: TransferOwnershipRequest,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    actor: OwnerOnly,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MembershipRead:
    from app.services import organization_service

    updated = await organization_service.transfer_clinic_ownership(
        db, clinic, actor, data.new_owner_membership_id
    )
    u = await db.get(User, updated.user_id)
    return MembershipRead(
        id=updated.id,
        user_id=updated.user_id,
        email=u.email if u else "",
        full_name=u.full_name if u else "",
        role=updated.role,
        is_active=updated.is_active,
    )


@router.patch("/{clinic_id}/members/{membership_id}", response_model=MembershipRead)
async def patch_member(
    membership_id: uuid.UUID,
    data: MembershipUpdate,
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    actor: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MembershipRead:
    from app.models import ClinicMembership

    target = await db.get(ClinicMembership, membership_id)
    if target is None or target.clinic_id != clinic.id:
        raise HTTPException(status_code=404, detail="Member not found")
    updated = await clinic_service.update_membership(db, target, data.role, data.is_active, user.id)
    u = await db.get(User, updated.user_id)
    return MembershipRead(
        id=updated.id,
        user_id=updated.user_id,
        email=u.email if u else "",
        full_name=u.full_name if u else "",
        role=updated.role,
        is_active=updated.is_active,
    )
