import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, DoctorProfile, Patient, Room, User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentRead,
    AppointmentReschedule,
    AppointmentUpdate,
    AvailableSlotList,
    NoShowRiskRead,
    WaitlistCreate,
    WaitlistRead,
    WaitlistUpdate,
)
from app.schemas.series import WalkInCreate
from app.schemas.visit import VisitStatusUpdate, WaitingRoomEntry, WaitingRoomResponse
from app.services import (
    appointment_service,
    slot_service,
    visit_service,
    waitlist_service,
    walkin_service,
)
from app.services.clinic_service import get_clinic
from app.services.no_show_risk_service import compute_no_show_risk
from app.services.recurring_service import SeriesScope, apply_series_scope

router = APIRouter(prefix="/appointments", tags=["appointments"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


async def _enrich_appointments(db: AsyncSession, items: list) -> list[AppointmentRead]:
    if not items:
        return []
    patient_ids = {a.patient_id for a in items}
    doctor_ids = {a.doctor_id for a in items}
    patients = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
    doctors = await db.execute(
        select(DoctorProfile, User)
        .join(User, User.id == DoctorProfile.user_id)
        .where(DoctorProfile.id.in_(doctor_ids))
    )
    patient_map = {p.id: p for p in patients.scalars()}
    doctor_map = {d.id: u.full_name for d, u in doctors.all()}
    room_ids = {a.room_id for a in items if a.room_id}
    room_map: dict = {}
    if room_ids:
        rooms = await db.execute(select(Room).where(Room.id.in_(room_ids)))
        room_map = {r.id: r.name for r in rooms.scalars()}
    out = []
    for a in items:
        row = AppointmentRead.model_validate(a)
        patient = patient_map.get(a.patient_id)
        row.patient_name = patient.full_name if patient else None
        row.doctor_name = doctor_map.get(a.doctor_id)
        row.room_name = room_map.get(a.room_id) if a.room_id else None
        if patient is not None:
            row.no_show_risk = NoShowRiskRead.model_validate(compute_no_show_risk(a, patient))
        out.append(row)
    return out


@router.get("", response_model=AppointmentListResponse)
async def list_appointments(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    doctor_id: uuid.UUID | None = None,
    patient_id: uuid.UUID | None = None,
    status: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    booking_source: str | None = None,
    room_id: uuid.UUID | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1, le=100),
    sort: str | None = None,
) -> AppointmentListResponse:
    items, total = await appointment_service.list_appointments(
        db,
        clinic_id,
        doctor_id,
        patient_id,
        status,
        start_from,
        start_to,
        booking_source=booking_source,
        room_id=room_id,
        q=q,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    enriched = await _enrich_appointments(db, items)
    return AppointmentListResponse(
        items=enriched,
        total=total,
        page=page,
        page_size=page_size or total or len(enriched),
    )


@router.get("/available-slots", response_model=AvailableSlotList)
async def staff_available_slots(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    doctor_id: uuid.UUID,
    on_date: date = Query(..., alias="date"),
    duration_minutes: int | None = None,
) -> AvailableSlotList:
    clinic = await get_clinic(db, clinic_id)
    slots = await slot_service.get_available_slots(db, clinic, doctor_id, on_date, duration_minutes)
    return AvailableSlotList(slots=slots)


@router.get("/waiting-room", response_model=WaitingRoomResponse)
async def get_waiting_room(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WaitingRoomResponse:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    items = await visit_service.list_waiting_room(db, clinic_id)
    enriched = await _enrich_appointments(db, items)
    today = datetime.now(ZoneInfo("Asia/Manila")).date().isoformat()
    return WaitingRoomResponse(
        items=[WaitingRoomEntry.model_validate(e) for e in enriched],
        date=today,
    )


@router.get("/waitlist", response_model=list[WaitlistRead])
async def get_waitlist(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = "waiting",
    doctor_id: uuid.UUID | None = None,
    preferred_date: date | None = None,
) -> list[WaitlistRead]:
    rows = await waitlist_service.list_waitlist(
        db,
        clinic_id,
        status=status,
        doctor_id=doctor_id,
        preferred_date=preferred_date,
    )
    return await waitlist_service.enrich_waitlist(db, rows)


@router.post("/waitlist", response_model=WaitlistRead)
async def post_waitlist(
    data: WaitlistCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WaitlistRead:
    entry = await waitlist_service.create_waitlist_entry(db, clinic_id, data, user.id)
    return (await waitlist_service.enrich_waitlist(db, [entry]))[0]


@router.patch("/waitlist/{entry_id}", response_model=WaitlistRead)
async def patch_waitlist(
    entry_id: uuid.UUID,
    data: WaitlistUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WaitlistRead:
    entry = await waitlist_service.update_waitlist_entry(db, clinic_id, entry_id, data, user.id)
    return (await waitlist_service.enrich_waitlist(db, [entry]))[0]


@router.post("/walk-in", response_model=AppointmentRead)
async def post_walk_in(
    data: WalkInCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    clinic = await get_clinic(db, clinic_id)
    appt = await walkin_service.create_walk_in(
        db,
        clinic,
        doctor_id=data.doctor_id,
        actor_id=user.id,
        patient_id=data.patient_id,
        new_patient=data.new_patient,
        reason_for_visit=data.reason_for_visit,
    )
    enriched = await _enrich_appointments(db, [appt])
    return enriched[0]


@router.post("", response_model=AppointmentRead)
async def create_appointment(
    data: AppointmentCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    clinic = await get_clinic(db, clinic_id)
    appt = await appointment_service.create_appointment(db, clinic, data, user.id)
    enriched = await _enrich_appointments(db, [appt])
    return enriched[0]


@router.get("/{appointment_id}", response_model=AppointmentRead)
async def get_appointment_detail(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    appt = await appointment_service.get_appointment(db, clinic_id, appointment_id)
    enriched = await _enrich_appointments(db, [appt])
    return enriched[0]


@router.post("/{appointment_id}/visit-status", response_model=AppointmentRead)
async def post_visit_status(
    appointment_id: uuid.UUID,
    data: VisitStatusUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    appt = await appointment_service.get_appointment(db, clinic_id, appointment_id)
    appt = await visit_service.transition_visit_status(db, appt, data.visit_status, user.id)
    enriched = await _enrich_appointments(db, [appt])
    return enriched[0]


@router.post("/{appointment_id}/mark-no-show", response_model=AppointmentRead)
async def post_mark_no_show(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    appt = await appointment_service.get_appointment(db, clinic_id, appointment_id)
    appt = await walkin_service.mark_no_show(db, appt, user.id)
    enriched = await _enrich_appointments(db, [appt])
    return enriched[0]


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentRead)
async def reschedule_appointment_route(
    appointment_id: uuid.UUID,
    data: AppointmentReschedule,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    clinic = await get_clinic(db, clinic_id)
    appt = await appointment_service.get_appointment(db, clinic_id, appointment_id)
    appt = await appointment_service.reschedule_appointment(
        db,
        clinic,
        appt,
        data.scheduled_start,
        data.scheduled_end,
        user.id,
    )
    enriched = await _enrich_appointments(db, [appt])
    return enriched[0]


@router.patch("/{appointment_id}", response_model=AppointmentRead)
async def patch_appointment(
    appointment_id: uuid.UUID,
    data: AppointmentUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    scope: SeriesScope = Query(default="this"),
) -> AppointmentRead:
    clinic = await get_clinic(db, clinic_id)
    appt = await appointment_service.get_appointment(db, clinic_id, appointment_id)
    targets = await apply_series_scope(db, appt, scope)
    updated = appt
    for target in targets:
        updated = await appointment_service.update_appointment(db, clinic, target, data, user.id)
    enriched = await _enrich_appointments(db, [updated])
    return enriched[0]


@router.delete("/{appointment_id}", response_model=AppointmentRead)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    scope: SeriesScope = Query(default="this"),
) -> AppointmentRead:
    clinic = await get_clinic(db, clinic_id)
    appt = await appointment_service.get_appointment(db, clinic_id, appointment_id)
    targets = await apply_series_scope(db, appt, scope)
    updated = appt
    for target in targets:
        updated = await appointment_service.update_appointment(
            db,
            clinic,
            target,
            AppointmentUpdate(appointment_status="Cancelled"),
            user.id,
        )
    enriched = await _enrich_appointments(db, [updated])
    return enriched[0]
