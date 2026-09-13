"""Insert synthetic clinic data for local UI review."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, hash_refresh_token
from app.models import (
    ActivityLog,
    AiAssistantAction,
    AiAssistantConversation,
    AiAssistantMessage,
    Appointment,
    AppointmentSeries,
    AppointmentWaitlist,
    BillingExtractionAttempt,
    Clinic,
    ClinicAiUsage,
    ClinicalOrder,
    ClinicMembership,
    ConsultationRecording,
    CreditNote,
    DoctorProfile,
    DocumentTemplate,
    EligibilityCheck,
    GeneratedDocument,
    InsuranceClaim,
    Invoice,
    InvoiceLineItem,
    LoaRequest,
    MembershipPlan,
    Notification,
    NotificationRead,
    Organization,
    OrganizationEnrolledClinic,
    OrganizationSubscription,
    Patient,
    PatientAssistantConversation,
    PatientAssistantMessage,
    PatientFile,
    PatientMedicalInfo,
    PatientMembership,
    PatientPortalToken,
    PatientRecall,
    PatientSurveyResponse,
    PatientVital,
    Payer,
    Payment,
    PlatformAuditLog,
    PlatformFeatureFlag,
    Prescription,
    PrescriptionItem,
    Reminder,
    Room,
    ServiceFee,
    SoapNote,
    StaffInvitation,
    User,
    VisitStatusEvent,
    VisitSummary,
)
from app.models.base import new_uuid
from app.seed.constants import (
    ADMIN_EMAIL,
    BIR_COMPLIANCE,
    BRANCH_CLINIC_NAME,
    BRANCH_CLINIC_SLUG,
    BRANCH_PATIENTS,
    BRANCH_RECEIPT_NUMBERING,
    BRANCH_SERVICE_FEES,
    CLINIC_NAME,
    CLINIC_SLUG,
    DEMO_PASSWORD,
    DOCTOR2_EMAIL,
    DOCTOR_B_EMAIL,
    GROWTH_SETTINGS,
    NOTIFICATION_PREFERENCES,
    ORG_NAME,
    ORG_SLUG,
    OWNER_EMAIL,
    PATIENTS,
    PLATFORM_EMAIL,
    RECEIPT_NUMBERING,
    RECEPTION_B_EMAIL,
    RECEPTION_EMAIL,
    SERVICE_FEES,
    SOAP_DIAGNOSES,
    WORKING_HOURS,
)

MANILA = ZoneInfo("Asia/Manila")


def manila_dt(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=MANILA).astimezone(UTC)


def _hash_token(raw: str) -> str:
    return hash_refresh_token(raw)


def today_open_hours(day: date) -> list[int]:
    weekday = day.weekday()
    if weekday == 6:
        return [9, 10, 11]
    if weekday == 5:
        return [9, 10, 11, 12]
    return [8, 9, 10, 11, 14, 15, 16]


@dataclass
class SeedResult:
    soap_notes: list[SoapNote] = field(default_factory=list)
    soap_note_ids: list[uuid.UUID] = field(default_factory=list)
    portal_verify_path: str | None = None
    portal_patient_email: str | None = None


async def _create_user(
    db: AsyncSession,
    *,
    email: str,
    full_name: str,
    now: datetime,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(DEMO_PASSWORD),
        full_name=full_name,
        email_verified_at=now,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


def _add_membership(db: AsyncSession, user: User, clinic: Clinic, role: str) -> None:
    db.add(
        ClinicMembership(
            user_id=user.id,
            clinic_id=clinic.id,
            role=role,
            is_active=True,
        )
    )


async def seed_demo_data(db: AsyncSession) -> SeedResult:
    now = datetime.now(UTC)
    today = datetime.now(MANILA).date()
    result = SeedResult()

    owner = await _create_user(db, email=OWNER_EMAIL, full_name="Dr. Maria Cruz", now=now)
    org = Organization(
        owner_id=owner.id,
        name=ORG_NAME,
        slug=ORG_SLUG,
        status="active",
    )
    db.add(org)
    await db.flush()
    db.add(
        OrganizationSubscription(
            organization_id=org.id,
            plan_key="clinic",
            status="active",
            trial_ends_at=None,
        )
    )

    clinic = Clinic(
        name=CLINIC_NAME,
        slug=CLINIC_SLUG,
        address="Unit 402, Ayala Triangle Gardens Tower, Makati City",
        contact_phone="+63281234567",
        contact_email="hello@makati-family-clinic.example",
        license_info="DOH-LIC-2024-00123",
        accreditation_info="PhilHealth accredited",
        working_hours=WORKING_HOURS,
        holiday_dates=["2026-12-25", "2026-12-30"],
        default_appointment_duration_minutes=30,
        onboarding_invite_skipped=True,
        onboarding_completed_at=now,
        public_booking_auto_confirm=True,
        reception_can_view_soap=False,
        receipt_numbering_config=RECEIPT_NUMBERING,
        notification_preferences=NOTIFICATION_PREFERENCES,
        recording_consent_enabled=True,
        ai_assistant_enabled=True,
        brand_color="#0F766E",
        organization_id=org.id,
        plan_key="clinic",
        status="active",
        bir_compliance_config=BIR_COMPLIANCE,
        growth_settings=GROWTH_SETTINGS,
    )
    branch = Clinic(
        name=BRANCH_CLINIC_NAME,
        slug=BRANCH_CLINIC_SLUG,
        address="5F High Street South Corporate Plaza, BGC, Taguig",
        contact_phone="+63281234568",
        contact_email="bgc@makati-family-clinic.example",
        license_info="DOH-LIC-2024-00124",
        accreditation_info="PhilHealth accredited",
        working_hours=WORKING_HOURS,
        holiday_dates=["2026-12-25", "2026-12-30"],
        default_appointment_duration_minutes=30,
        onboarding_invite_skipped=True,
        onboarding_completed_at=now,
        public_booking_auto_confirm=True,
        reception_can_view_soap=False,
        receipt_numbering_config=BRANCH_RECEIPT_NUMBERING,
        notification_preferences={
            **NOTIFICATION_PREFERENCES,
            "sender_name": BRANCH_CLINIC_NAME,
        },
        recording_consent_enabled=True,
        ai_assistant_enabled=True,
        brand_color="#1D4ED8",
        organization_id=org.id,
        plan_key="clinic",
        status="active",
        bir_compliance_config=BIR_COMPLIANCE,
        growth_settings=GROWTH_SETTINGS,
    )
    db.add_all([clinic, branch])
    await db.flush()
    db.add_all(
        [
            OrganizationEnrolledClinic(
                organization_id=org.id,
                clinic_id=clinic.id,
                status="active",
                enrolled_at=now - timedelta(days=120),
            ),
            OrganizationEnrolledClinic(
                organization_id=org.id,
                clinic_id=branch.id,
                status="active",
                enrolled_at=now - timedelta(days=40),
            ),
        ]
    )

    doctor2 = await _create_user(db, email=DOCTOR2_EMAIL, full_name="Dr. James Santos", now=now)
    reception = await _create_user(db, email=RECEPTION_EMAIL, full_name="Liza Reyes", now=now)
    admin = await _create_user(db, email=ADMIN_EMAIL, full_name="Mark Villanueva", now=now)
    platform = await _create_user(db, email=PLATFORM_EMAIL, full_name="Alex Rivera", now=now)
    doctor_b = await _create_user(db, email=DOCTOR_B_EMAIL, full_name="Dr. Nina Reyes", now=now)
    reception_b = await _create_user(
        db, email=RECEPTION_B_EMAIL, full_name="Carlo Mendoza", now=now
    )

    _add_membership(db, owner, clinic, "owner")
    _add_membership(db, owner, branch, "owner")
    _add_membership(db, doctor2, clinic, "doctor")
    _add_membership(db, reception, clinic, "reception")
    _add_membership(db, admin, clinic, "admin")
    _add_membership(db, admin, branch, "admin")
    _add_membership(db, platform, clinic, "admin")
    _add_membership(db, doctor_b, branch, "doctor")
    _add_membership(db, reception_b, branch, "reception")

    owner_profile = DoctorProfile(
        user_id=owner.id,
        clinic_id=clinic.id,
        specialty="Family Medicine",
        prc_license_number="PRC-123456",
        consultation_fee=Decimal("500.00"),
        follow_up_fee=Decimal("350.00"),
        default_appointment_duration_minutes=30,
    )
    doctor2_profile = DoctorProfile(
        user_id=doctor2.id,
        clinic_id=clinic.id,
        specialty="Internal Medicine",
        prc_license_number="PRC-654321",
        consultation_fee=Decimal("600.00"),
        follow_up_fee=Decimal("400.00"),
        default_appointment_duration_minutes=30,
    )
    doctor_b_profile = DoctorProfile(
        user_id=doctor_b.id,
        clinic_id=branch.id,
        specialty="Pediatrics",
        prc_license_number="PRC-778899",
        consultation_fee=Decimal("600.00"),
        follow_up_fee=Decimal("400.00"),
        default_appointment_duration_minutes=30,
    )
    db.add_all([owner_profile, doctor2_profile, doctor_b_profile])
    await db.flush()

    for name, amount, category, duration in SERVICE_FEES:
        db.add(
            ServiceFee(
                clinic_id=clinic.id,
                name=name,
                amount=amount,
                category=category,
                duration_minutes=duration,
            )
        )
    for name, amount, category, duration in BRANCH_SERVICE_FEES:
        db.add(
            ServiceFee(
                clinic_id=branch.id,
                name=name,
                amount=amount,
                category=category,
                duration_minutes=duration,
            )
        )

    room_a = Room(clinic_id=clinic.id, name="Room 1", is_active=True, created_at=now)
    room_b = Room(clinic_id=clinic.id, name="Room 2", is_active=True, created_at=now)
    room_inactive = Room(
        clinic_id=clinic.id, name="Room 3 (storage)", is_active=False, created_at=now
    )
    room_bgc = Room(clinic_id=branch.id, name="Consult 1", is_active=True, created_at=now)
    db.add_all([room_a, room_b, room_inactive, room_bgc])
    await db.flush()

    db.add_all(
        [
            StaffInvitation(
                clinic_id=clinic.id,
                email="nurse.pending@example.com",
                role="reception",
                invited_by_user_id=owner.id,
                token_hash=_hash_token(secrets.token_urlsafe(32)),
                expires_at=now + timedelta(days=7),
                created_at=now,
            ),
            StaffInvitation(
                clinic_id=clinic.id,
                email="dr.invite@example.com",
                role="doctor",
                invited_by_user_id=admin.id,
                token_hash=_hash_token(secrets.token_urlsafe(32)),
                expires_at=now + timedelta(days=5),
                created_at=now - timedelta(days=1),
            ),
            StaffInvitation(
                clinic_id=clinic.id,
                email="expired.invite@example.com",
                role="reception",
                invited_by_user_id=owner.id,
                token_hash=_hash_token(secrets.token_urlsafe(32)),
                expires_at=now - timedelta(days=2),
                created_at=now - timedelta(days=10),
            ),
            StaffInvitation(
                clinic_id=branch.id,
                email="bgc.front@example.com",
                role="reception",
                invited_by_user_id=owner.id,
                token_hash=_hash_token(secrets.token_urlsafe(32)),
                expires_at=now + timedelta(days=7),
                created_at=now,
            ),
        ]
    )

    templates = await _seed_document_templates(db, clinic, branch, now)
    await _seed_payers(db, clinic)
    membership_plan = MembershipPlan(
        clinic_id=clinic.id,
        name="Family care monthly",
        price=Decimal("1499.00"),
        billing_interval="monthly",
        included_services=[
            {"category": "consultation", "count_per_period": 2},
            {"category": "lab", "count_per_period": 1},
        ],
        is_active=True,
    )
    db.add(membership_plan)
    await db.flush()

    patients = await _seed_patients(db, clinic, PATIENTS, owner.id, now)
    branch_patients = await _seed_patients(db, branch, BRANCH_PATIENTS, owner.id, now)

    helena = next(p for p in patients if p.full_name == "Helena Go")
    db.add(
        PatientMembership(
            clinic_id=clinic.id,
            patient_id=helena.id,
            plan_id=membership_plan.id,
            status="active",
            started_at=today - timedelta(days=20),
            current_period_end=today + timedelta(days=10),
            usage_this_period={"consultation": 1},
        )
    )

    appointments, completed_appts = await _seed_appointments(
        db,
        clinic=clinic,
        branch=branch,
        patients=patients,
        branch_patients=branch_patients,
        owner=owner,
        reception=reception,
        owner_profile=owner_profile,
        doctor2_profile=doctor2_profile,
        doctor_b_profile=doctor_b_profile,
        room_a=room_a,
        room_b=room_b,
        room_bgc=room_bgc,
        today=today,
        now=now,
    )

    soap_notes = await _seed_clinical(
        db,
        clinic=clinic,
        patients=patients,
        appointments=appointments,
        completed_appts=completed_appts,
        owner=owner,
        doctor2=doctor2,
        reception=reception,
        owner_profile=owner_profile,
        doctor2_profile=doctor2_profile,
        templates=templates,
        now=now,
        today=today,
    )
    result.soap_notes = soap_notes
    result.soap_note_ids = [note.id for note in soap_notes]

    await _seed_billing(
        db,
        clinic=clinic,
        branch=branch,
        patients=patients,
        branch_patients=branch_patients,
        completed_appts=completed_appts,
        owner=owner,
        admin=admin,
        reception=reception,
        reception_b=reception_b,
        now=now,
    )

    await _seed_communications(
        db,
        result=result,
        clinic=clinic,
        patients=patients,
        appointments=appointments,
        completed_appts=completed_appts,
        owner=owner,
        doctor2=doctor2,
        reception=reception,
        admin=admin,
        now=now,
        today=today,
    )

    await _seed_platform(db, org=org, clinic=clinic, branch=branch, platform=platform, now=now)
    await db.commit()
    return result


async def _seed_document_templates(
    db: AsyncSession, clinic: Clinic, branch: Clinic, now: datetime
) -> dict[str, DocumentTemplate]:
    specs = [
        (
            "medical_certificate",
            "Medical certificate",
            "<p>This is to certify that {{patient.full_name}} was examined on {{visit.date}}.</p>",
        ),
        (
            "referral_letter",
            "Referral letter",
            "<p>Referring {{patient.full_name}} to a specialist for further evaluation.</p>",
        ),
        (
            "lab_request",
            "Lab request",
            "<p>Please perform the requested laboratory studies for {{patient.full_name}}.</p>",
        ),
        (
            "confinement_certificate",
            "Confinement certificate",
            "<p>{{patient.full_name}} was confined and may resume usual activity as advised.</p>",
        ),
    ]
    templates: dict[str, DocumentTemplate] = {}
    for key, name, body in specs:
        row = DocumentTemplate(
            clinic_id=clinic.id,
            template_key=key,
            name=name,
            template_type=key,
            schema_version=1,
            body={},
            body_template=body,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        templates[key] = row
    db.add(
        DocumentTemplate(
            clinic_id=branch.id,
            template_key="medical_certificate",
            name="Medical certificate",
            template_type="medical_certificate",
            schema_version=1,
            body={},
            body_template="<p>This is to certify that {{patient.full_name}} was examined.</p>",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
    )
    await db.flush()
    return templates


async def _seed_payers(db: AsyncSession, clinic: Clinic) -> list[Payer]:
    rows = [
        Payer(clinic_id=clinic.id, name="Maxicare", payer_type="hmo", is_active=True),
        Payer(clinic_id=clinic.id, name="Medicard", payer_type="hmo", is_active=True),
        Payer(clinic_id=clinic.id, name="Intellicare", payer_type="hmo", is_active=True),
        Payer(clinic_id=clinic.id, name="PhilHealth", payer_type="philhealth", is_active=True),
        Payer(clinic_id=clinic.id, name="Legacy HMO", payer_type="hmo", is_active=False),
    ]
    db.add_all(rows)
    await db.flush()
    return rows


async def _seed_patients(
    db: AsyncSession,
    clinic: Clinic,
    fixtures: list,
    created_by: uuid.UUID,
    now: datetime,
) -> list[Patient]:
    rows: list[Patient] = []
    for idx, fixture in enumerate(fixtures, start=1):
        patient = Patient(
            clinic_id=clinic.id,
            patient_number=idx,
            full_name=fixture.full_name,
            birthdate=fixture.birthdate,
            sex=fixture.sex,
            civil_status=fixture.civil_status,
            occupation=fixture.occupation,
            contact_number=fixture.contact_number,
            email=fixture.email,
            address="Makati City, Metro Manila"
            if clinic.slug == CLINIC_SLUG
            else "BGC, Taguig, Metro Manila",
            emergency_contact={"name": "Family contact", "phone": fixture.contact_number},
            insurance_info=fixture.insurance_info,
            created_by_user_id=created_by,
            data_processing_consent_at=now - timedelta(days=120),
            no_show_count=fixture.no_show_count,
            is_archived=fixture.is_archived,
            reminders_opted_out=fixture.reminders_opted_out,
        )
        db.add(patient)
        await db.flush()
        rows.append(patient)
        meds = (
            [{"name": "Amlodipine 5mg", "frequency": "OD"}]
            if "Hypertension" in fixture.chronic_conditions
            else []
        )
        if "Type 2 Diabetes" in fixture.chronic_conditions:
            meds.append({"name": "Metformin 500mg", "frequency": "BID"})
        db.add(
            PatientMedicalInfo(
                patient_id=patient.id,
                clinic_id=clinic.id,
                allergies_reviewed=True,
                allergies=fixture.allergies,
                medical_history=fixture.medical_history,
                family_history=fixture.family_history,
                surgical_history=fixture.surgical_history,
                chronic_conditions=fixture.chronic_conditions,
                current_medications=meds,
                vaccination_history=list(fixture.vaccination_history),
            )
        )
    await db.flush()
    return rows


async def _seed_appointments(
    db: AsyncSession,
    *,
    clinic: Clinic,
    branch: Clinic,
    patients: list[Patient],
    branch_patients: list[Patient],
    owner: User,
    reception: User,
    owner_profile: DoctorProfile,
    doctor2_profile: DoctorProfile,
    doctor_b_profile: DoctorProfile,
    room_a: Room,
    room_b: Room,
    room_bgc: Room,
    today: date,
    now: datetime,
) -> tuple[list[Appointment], list[Appointment]]:
    appointments: list[Appointment] = []
    doctors = [owner_profile, doctor2_profile]
    doctor_day_hour: dict[tuple[uuid.UUID, date], int] = {}

    def next_hour(doctor_id: uuid.UUID, day: date, start: int = 8) -> int:
        key = (doctor_id, day)
        hour = doctor_day_hour.get(key, start)
        doctor_day_hour[key] = hour + 1
        return hour

    def add_appointment(
        patient: Patient,
        doctor: DoctorProfile,
        day: date,
        hour: int | None = None,
        *,
        clinic_row: Clinic = clinic,
        status: str = "Confirmed",
        visit_status: str | None = None,
        reason: str = "Follow-up",
        room: Room | None = None,
        booking_source: str = "staff",
        duration: int = 30,
        created_by: uuid.UUID | None = None,
        notes: str | None = None,
        minute: int = 0,
    ) -> Appointment:
        slot_hour = hour if hour is not None else next_hour(doctor.id, day)
        start = manila_dt(day, slot_hour, minute)
        end = start + timedelta(minutes=duration)
        appt = Appointment(
            clinic_id=clinic_row.id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            room_id=room.id if room else None,
            scheduled_start=start,
            scheduled_end=end,
            reason_for_visit=reason,
            notes=notes,
            appointment_status=status,
            current_visit_status=visit_status,
            booking_source=booking_source,
            created_by_user_id=created_by or owner.id,
        )
        db.add(appt)
        appointments.append(appt)
        return appt

    hours = today_open_hours(today)
    h0 = hours[0]
    h1 = hours[1] if len(hours) > 1 else hours[0]
    h2 = hours[2] if len(hours) > 2 else hours[-1]
    h3 = hours[3] if len(hours) > 3 else hours[-1]

    add_appointment(
        patients[0],
        owner_profile,
        today,
        h0,
        status="Confirmed",
        visit_status="Arrived",
        reason="BP check",
        room=room_a,
    )
    add_appointment(
        patients[4],
        owner_profile,
        today,
        h1,
        status="Confirmed",
        visit_status="In Consultation",
        reason="Migraine follow-up",
        room=room_a,
    )
    add_appointment(
        patients[2],
        doctor2_profile,
        today,
        h0,
        status="Confirmed",
        visit_status="Arrived",
        reason="Pediatric consult",
        room=room_b,
    )
    add_appointment(
        patients[6],
        doctor2_profile,
        today,
        h1,
        status="Scheduled",
        reason="Prenatal visit",
        room=room_b,
    )
    add_appointment(
        patients[9],
        owner_profile,
        today,
        h2,
        status="Confirmed",
        reason="Back pain",
        booking_source="public_link",
    )
    if len(hours) > 3:
        add_appointment(
            patients[11],
            owner_profile,
            today,
            h3,
            status="Scheduled",
            reason="Gout flare",
        )
    if len(hours) > 2:
        add_appointment(
            patients[1],
            doctor2_profile,
            today,
            h2,
            status="Confirmed",
            reason="Diabetes follow-up",
        )
    walk_in_hour = h3 if len(hours) > 3 else (hours[1] if len(hours) > 1 else h0)
    walk_in_minute = 0 if len(hours) > 3 else 30
    add_appointment(
        patients[7],
        doctor2_profile,
        today,
        walk_in_hour,
        minute=walk_in_minute,
        status="Confirmed",
        visit_status="Arrived",
        reason="Walk-in: asthma",
        notes="Walk-in at desk",
        created_by=reception.id,
    )
    add_appointment(
        patients[10],
        owner_profile,
        today,
        h1,
        minute=30,
        status="Cancelled",
        reason="School clearance",
        notes="Patient cancelled this morning",
    )
    add_appointment(
        patients[14],
        doctor2_profile,
        today,
        h0,
        minute=30,
        status="No Show",
        reason="UTI follow-up",
    )
    rescheduled = add_appointment(
        patients[3],
        owner_profile,
        today,
        h2,
        minute=30,
        status="Rescheduled",
        reason="Allergic rhinitis",
    )
    add_appointment(
        patients[3],
        owner_profile,
        today + timedelta(days=2 if today.weekday() != 5 else 3),
        10,
        status="Scheduled",
        reason="Allergic rhinitis (rescheduled)",
        notes=f"Moved from {rescheduled.scheduled_start.date()}",
        booking_source="ai_assistant",
    )

    add_appointment(
        branch_patients[0],
        doctor_b_profile,
        today,
        h0,
        clinic_row=branch,
        status="Confirmed",
        visit_status="Arrived",
        reason="Well-child",
        room=room_bgc,
        created_by=owner.id,
    )
    add_appointment(
        branch_patients[1],
        doctor_b_profile,
        today,
        h1,
        clinic_row=branch,
        status="Confirmed",
        reason="Asthma review",
        room=room_bgc,
    )

    for offset in range(1, 46):
        past_day = today - timedelta(days=offset)
        if past_day.weekday() == 6:
            continue
        patient = patients[offset % len(patients)]
        if patient.is_archived:
            continue
        doctor = doctors[offset % 2]
        add_appointment(
            patient,
            doctor,
            past_day,
            status="Confirmed",
            visit_status="Completed" if offset % 2 == 0 else None,
            reason="Routine visit",
            booking_source="public_link" if offset % 4 == 0 else "staff",
        )
        if offset % 3 == 0:
            add_appointment(
                patients[(offset + 5) % len(patients)],
                doctors[(offset + 1) % 2],
                past_day,
                status="No Show" if offset == 15 else "Confirmed",
                visit_status="Completed" if offset % 5 == 0 else None,
                reason="Follow-up",
            )
        if offset == 8:
            add_appointment(
                patients[12],
                owner_profile,
                past_day,
                16,
                status="Cancelled",
                reason="Acne consult",
            )

    for i in range(8):
        future_day = today + timedelta(days=1 + i)
        if future_day.weekday() == 6:
            continue
        add_appointment(
            patients[i % len(patients)],
            doctors[i % 2],
            future_day,
            status="Scheduled" if i % 2 else "Confirmed",
            reason="Scheduled follow-up",
            booking_source="public_assistant" if i == 3 else "staff",
        )

    await db.flush()

    series = AppointmentSeries(
        clinic_id=clinic.id,
        doctor_id=owner_profile.id,
        patient_id=patients[0].id,
        rrule_string="FREQ=WEEKLY;BYDAY=MO;COUNT=8",
        series_start=manila_dt(today + timedelta(days=7), 10),
        duration_minutes=30,
        reason_for_visit="Hypertension monitoring",
        created_by_user_id=owner.id,
    )
    db.add(series)
    await db.flush()
    occ = 0
    day = today + timedelta(days=7)
    while occ < 3:
        while day.weekday() != 0:
            day += timedelta(days=1)
        add_appointment(
            patients[0],
            owner_profile,
            day,
            hour=10,
            status="Scheduled",
            reason="Hypertension monitoring",
        )
        appointments[-1].series_id = series.id
        appointments[-1].series_occurrence_index = occ
        occ += 1
        day += timedelta(days=7)

    db.add(
        AppointmentWaitlist(
            clinic_id=clinic.id,
            patient_id=patients[8].id,
            doctor_id=owner_profile.id,
            preferred_date=today + timedelta(days=3),
            notes="Prefers morning slot",
            status="waiting",
            created_by_user_id=reception.id,
        )
    )
    db.add(
        AppointmentWaitlist(
            clinic_id=clinic.id,
            patient_id=patients[5].id,
            doctor_id=doctor2_profile.id,
            preferred_date=today + timedelta(days=1),
            notes="Any afternoon",
            status="cancelled",
            created_by_user_id=reception.id,
        )
    )
    booked_future = next(
        (
            a
            for a in appointments
            if a.appointment_status == "Scheduled" and a.scheduled_start > now
        ),
        None,
    )
    db.add(
        AppointmentWaitlist(
            clinic_id=clinic.id,
            patient_id=patients[16].id if len(patients) > 16 else patients[3].id,
            doctor_id=owner_profile.id,
            preferred_date=today + timedelta(days=5),
            status="booked",
            booked_appointment_id=booked_future.id if booked_future else None,
            created_by_user_id=reception.id,
        )
    )

    await db.flush()

    for appt in appointments:
        if appt.current_visit_status:
            db.add(
                VisitStatusEvent(
                    appointment_id=appt.id,
                    clinic_id=appt.clinic_id,
                    visit_status="Arrived",
                    changed_at=appt.scheduled_start - timedelta(minutes=10),
                    changed_by_user_id=reception.id,
                )
            )
            if appt.current_visit_status in ("In Consultation", "Completed"):
                db.add(
                    VisitStatusEvent(
                        appointment_id=appt.id,
                        clinic_id=appt.clinic_id,
                        visit_status="In Consultation",
                        changed_at=appt.scheduled_start,
                        changed_by_user_id=owner.id,
                    )
                )
            if appt.current_visit_status == "Completed":
                db.add(
                    VisitStatusEvent(
                        appointment_id=appt.id,
                        clinic_id=appt.clinic_id,
                        visit_status="Completed",
                        changed_at=appt.scheduled_end,
                        changed_by_user_id=owner.id,
                    )
                )

    completed_appts = [
        a
        for a in appointments
        if a.clinic_id == clinic.id
        and (
            a.current_visit_status == "Completed"
            or (a.scheduled_start < manila_dt(today, 0) and a.appointment_status == "Confirmed")
        )
    ]
    await db.flush()
    return appointments, completed_appts


def _specialty_for_patient(patient: Patient) -> tuple[str, dict]:
    name = patient.full_name
    if name in {"Ana Reyes", "Sofia Cruz", "Miguel Torres", "Victor Ramos"}:
        if name == "Victor Ramos":
            return "dental", {
                "schema_version": 1,
                "template_key": "dental",
                "tooth_numbers": [36, 37],
                "teeth": "Occlusal caries 36, 37",
            }
        return "pediatric", {
            "schema_version": 1,
            "template_key": "pediatric",
            "height_cm": "112",
            "weight_kg": "19.5",
            "growth_percentile": "55",
        }
    if name == "Patricia Lim":
        return "obgyn", {
            "schema_version": 1,
            "template_key": "obgyn",
            "gravida": "1",
            "para": "0",
            "lmp": "2026-02-10",
            "edd": "2026-11-17",
        }
    if name == "Paolo Navarro":
        return "psychiatry", {
            "schema_version": 1,
            "template_key": "psychiatry",
            "mental_status": "Anxious affect, oriented x3",
            "risk": "Low",
        }
    if name in {"Isabel Ramos", "Camille Sy"}:
        return "dermatology", {
            "schema_version": 1,
            "template_key": "dermatology",
            "lesion_location": "Cheeks and chin",
            "morphology": "Inflammatory papules",
        }
    return "general", {"schema_version": 1, "template_key": "general"}


async def _seed_clinical(
    db: AsyncSession,
    *,
    clinic: Clinic,
    patients: list[Patient],
    appointments: list[Appointment],
    completed_appts: list[Appointment],
    owner: User,
    doctor2: User,
    reception: User,
    owner_profile: DoctorProfile,
    doctor2_profile: DoctorProfile,
    templates: dict[str, DocumentTemplate],
    now: datetime,
    today: date,
) -> list[SoapNote]:
    doctor_user = {owner_profile.id: owner.id, doctor2_profile.id: doctor2.id}
    soap_notes: list[SoapNote] = []
    by_id = {p.id: p for p in patients}

    for i, appt in enumerate(completed_appts[:28]):
        diag = SOAP_DIAGNOSES[i % len(SOAP_DIAGNOSES)]
        patient = by_id.get(appt.patient_id)
        template_key, specialty_data = (
            _specialty_for_patient(patient) if patient else ("general", {})
        )
        actor_id = doctor_user.get(appt.doctor_id, owner.id)
        note = SoapNote(
            appointment_id=appt.id,
            patient_id=appt.patient_id,
            doctor_id=appt.doctor_id,
            clinic_id=clinic.id,
            version_number=1,
            subjective=diag[1],
            objective=diag[2],
            assessment=diag[3],
            plan=diag[4],
            diagnosis_primary=diag[0],
            icd10_codes=[diag[5]],
            follow_up_date=today + timedelta(days=14),
            specialty_template_key=template_key,
            specialty_data=specialty_data,
            signed_at=appt.scheduled_end + timedelta(minutes=5) if i % 2 == 0 else None,
            created_by_user_id=actor_id,
            created_at=appt.scheduled_end,
        )
        db.add(note)
        soap_notes.append(note)
        db.add(
            PatientVital(
                patient_id=appt.patient_id,
                clinic_id=clinic.id,
                recorded_at=appt.scheduled_start,
                height_cm=Decimal("165.00"),
                weight_kg=Decimal("68.50"),
                bmi=Decimal("25.10"),
                blood_pressure="128/82",
                temperature_c=Decimal("36.8"),
                heart_rate=78,
                respiratory_rate=16,
                spo2=98,
                recorded_by_user_id=reception.id,
                visit_id=appt.id,
            )
        )

    await db.flush()
    if soap_notes:
        first = soap_notes[0]
        db.add(
            SoapNote(
                appointment_id=first.appointment_id,
                patient_id=first.patient_id,
                doctor_id=first.doctor_id,
                clinic_id=clinic.id,
                version_number=2,
                subjective=first.subjective,
                objective=first.objective,
                assessment=first.assessment,
                plan="Updated plan: recheck labs before next visit.",
                diagnosis_primary=first.diagnosis_primary,
                icd10_codes=first.icd10_codes,
                follow_up_date=first.follow_up_date,
                specialty_template_key=first.specialty_template_key,
                specialty_data=first.specialty_data,
                signed_at=now - timedelta(days=1),
                created_by_user_id=owner.id,
                created_at=now - timedelta(days=1),
            )
        )

    issued_rx = Prescription(
        patient_id=patients[0].id,
        doctor_id=owner_profile.id,
        clinic_id=clinic.id,
        appointment_id=completed_appts[0].id if completed_appts else None,
        status="issued",
        notes="Take with food.",
        issued_at=now - timedelta(days=3),
        created_by_user_id=owner.id,
    )
    db.add(issued_rx)
    await db.flush()
    db.add_all(
        [
            PrescriptionItem(
                prescription_id=issued_rx.id,
                drug_name="Amlodipine",
                generic_name="Amlodipine",
                dosage="5 mg",
                form="tablet",
                frequency="Once daily",
                duration="30 days",
                quantity="30",
                sort_order=0,
            ),
            PrescriptionItem(
                prescription_id=issued_rx.id,
                drug_name="Losartan",
                generic_name="Losartan",
                dosage="50 mg",
                form="tablet",
                frequency="Once daily",
                duration="30 days",
                quantity="30",
                sort_order=1,
            ),
        ]
    )

    draft_rx = Prescription(
        patient_id=patients[4].id,
        doctor_id=owner_profile.id,
        clinic_id=clinic.id,
        status="draft",
        created_by_user_id=owner.id,
    )
    db.add(draft_rx)
    await db.flush()
    db.add(
        PrescriptionItem(
            prescription_id=draft_rx.id,
            drug_name="Sumatriptan",
            generic_name="Sumatriptan",
            dosage="50 mg",
            form="tablet",
            frequency="PRN",
            duration="As needed",
            quantity="6",
            sort_order=0,
        )
    )

    voided_rx = Prescription(
        patient_id=patients[7].id,
        doctor_id=doctor2_profile.id,
        clinic_id=clinic.id,
        status="voided",
        notes="Wrong patient selected",
        issued_at=now - timedelta(days=10),
        voided_at=now - timedelta(days=9),
        void_reason="Issued to wrong chart",
        created_by_user_id=doctor2.id,
    )
    db.add(voided_rx)
    await db.flush()
    db.add(
        PrescriptionItem(
            prescription_id=voided_rx.id,
            drug_name="Salbutamol",
            generic_name="Salbutamol",
            dosage="100 mcg",
            form="inhaler",
            frequency="2 puffs PRN",
            duration="30 days",
            quantity="1",
            sort_order=0,
        )
    )

    lab_file = PatientFile(
        patient_id=patients[1].id,
        clinic_id=clinic.id,
        r2_key=f"seed/{clinic.id}/{patients[1].id}/lab-result.pdf",
        file_type="lab_result",
        description="HbA1c result",
        uploaded_by_user_id=owner.id,
        uploaded_at=now - timedelta(days=8),
        visit_id=completed_appts[1].id if len(completed_appts) > 1 else None,
    )
    imaging_file = PatientFile(
        patient_id=patients[9].id,
        clinic_id=clinic.id,
        r2_key=f"seed/{clinic.id}/{patients[9].id}/lumbosacral-xray.pdf",
        file_type="imaging",
        description="Lumbosacral X-ray",
        uploaded_by_user_id=reception.id,
        uploaded_at=now - timedelta(days=12),
    )
    db.add_all([lab_file, imaging_file])
    await db.flush()

    order_specs = [
        ("lab", "HbA1c", "resulted", "HbA1c 7.8%", patients[1], lab_file.id),
        ("lab", "CBC", "ordered", None, patients[0], None),
        ("imaging", "Chest X-ray", "in_progress", None, patients[5], None),
        ("lab", "Urinalysis", "cancelled", "Patient deferred", patients[14], None),
    ]
    for order_type, name, status, summary, patient, file_id in order_specs:
        db.add(
            ClinicalOrder(
                clinic_id=clinic.id,
                patient_id=patient.id,
                appointment_id=completed_appts[0].id if completed_appts else None,
                order_type=order_type,
                name=name,
                status=status,
                result_summary=summary,
                patient_file_id=file_id,
                created_by_user_id=owner.id,
            )
        )

    db.add(
        GeneratedDocument(
            clinic_id=clinic.id,
            patient_id=patients[3].id,
            template_id=templates["medical_certificate"].id,
            document_type="medical_certificate",
            status="draft",
            preview_content=f"Medical certificate draft for {patients[3].full_name}.",
            created_by_user_id=owner.id,
        )
    )
    db.add(
        GeneratedDocument(
            clinic_id=clinic.id,
            patient_id=patients[1].id,
            appointment_id=completed_appts[1].id if len(completed_appts) > 1 else None,
            template_id=templates["referral_letter"].id,
            document_type="referral_letter",
            status="issued",
            preview_content="Referral for endocrinology consult.",
            final_content_snapshot=(
                "Referral for endocrinology consult. Patient has uncontrolled diabetes."
            ),
            issued_by_user_id=owner.id,
            issued_at=now - timedelta(days=6),
            created_by_user_id=owner.id,
            referral_recipient="Dr. Ana Endocrinology, St. Luke's",
            referral_status="sent",
            referral_outcome=None,
        )
    )
    db.add(
        GeneratedDocument(
            clinic_id=clinic.id,
            patient_id=patients[0].id,
            template_id=templates["lab_request"].id,
            document_type="lab_request",
            status="issued",
            preview_content="Lab request: HbA1c, lipid profile.",
            final_content_snapshot="Lab request: HbA1c, lipid profile.",
            issued_by_user_id=owner.id,
            issued_at=now - timedelta(days=4),
            created_by_user_id=owner.id,
        )
    )

    if completed_appts:
        db.add(
            VisitSummary(
                clinic_id=clinic.id,
                appointment_id=completed_appts[0].id,
                generated_text="Visit summary: BP discussed. Continue current medications.",
                edited_text="BP discussed. Continue amlodipine. Recheck in 2 weeks.",
                status="sent",
                reviewed_by_user_id=owner.id,
                sent_at=now - timedelta(hours=20),
                created_at=now - timedelta(days=1),
            )
        )
        if len(completed_appts) > 1:
            db.add(
                VisitSummary(
                    clinic_id=clinic.id,
                    appointment_id=completed_appts[1].id,
                    generated_text="Draft summary for diabetes follow-up.",
                    status="draft",
                    created_at=now - timedelta(hours=6),
                )
            )
        if len(completed_appts) > 2:
            db.add(
                VisitSummary(
                    clinic_id=clinic.id,
                    appointment_id=completed_appts[2].id,
                    generated_text="",
                    generation_failed=True,
                    status="draft",
                    created_at=now - timedelta(hours=3),
                )
            )

        db.add(
            ConsultationRecording(
                appointment_id=completed_appts[2].id
                if len(completed_appts) > 2
                else completed_appts[0].id,
                clinic_id=clinic.id,
                r2_key=f"seed/{clinic.id}/recording-001.webm",
                duration_seconds=420,
                transcription_status="done",
                transcript_text=(
                    "Patient reports headache for three days. No fever. "
                    "Plan: symptomatic treatment and follow up if worse."
                ),
                created_by_user_id=owner.id,
                created_at=now - timedelta(days=2),
            )
        )
        db.add(
            ConsultationRecording(
                appointment_id=completed_appts[0].id,
                clinic_id=clinic.id,
                r2_key=f"seed/{clinic.id}/recording-002.webm",
                duration_seconds=90,
                transcription_status="pending",
                created_by_user_id=owner.id,
                created_at=now - timedelta(hours=2),
            )
        )
        if len(completed_appts) > 3:
            db.add(
                ConsultationRecording(
                    appointment_id=completed_appts[3].id,
                    clinic_id=clinic.id,
                    r2_key=f"seed/{clinic.id}/recording-003.webm",
                    duration_seconds=60,
                    transcription_status="failed",
                    created_by_user_id=doctor2.id,
                    created_at=now - timedelta(days=5),
                )
            )

    await db.flush()
    return soap_notes


async def _seed_billing(
    db: AsyncSession,
    *,
    clinic: Clinic,
    branch: Clinic,
    patients: list[Patient],
    branch_patients: list[Patient],
    completed_appts: list[Appointment],
    owner: User,
    admin: User,
    reception: User,
    reception_b: User,
    now: datetime,
) -> list[Invoice]:
    invoice_specs: list[
        tuple[str, str | None, list[tuple[str, Decimal, str]], list[tuple[str, Decimal]] | None]
    ] = [
        (
            "issued",
            "INV-0040",
            [("General consultation", Decimal("500.00"), "consultation")],
            [("cash", Decimal("500.00"))],
        ),
        (
            "partially_paid",
            "INV-0041",
            [("ECG", Decimal("450.00"), "procedure"), ("CBC panel", Decimal("350.00"), "lab")],
            [("gcash", Decimal("400.00"))],
        ),
        (
            "paid",
            "INV-0039",
            [("Follow-up visit", Decimal("350.00"), "consultation")],
            [("cash", Decimal("350.00"))],
        ),
        ("draft", None, [("Urinalysis", Decimal("150.00"), "lab")], None),
        (
            "void",
            "INV-0038",
            [("General consultation", Decimal("500.00"), "consultation")],
            None,
        ),
        (
            "issued",
            "INV-0042",
            [("Prenatal consult", Decimal("700.00"), "consultation")],
            None,
        ),
        (
            "paid",
            "INV-0043",
            [("Pediatric consult", Decimal("550.00"), "consultation")],
            [("card", Decimal("550.00"))],
        ),
        (
            "partially_paid",
            "INV-0044",
            [("General consultation", Decimal("500.00"), "consultation")],
            [("bank_transfer", Decimal("200.00"))],
        ),
        (
            "issued",
            "INV-0045",
            [("Nebulization", Decimal("400.00"), "procedure")],
            None,
        ),
    ]

    invoices: list[Invoice] = []
    for i, (status, number, lines, payments) in enumerate(invoice_specs):
        patient = patients[i % len(patients)]
        appt = completed_appts[i] if i < len(completed_appts) else None
        subtotal = sum(amount for _, amount, _ in lines)
        invoice = Invoice(
            clinic_id=clinic.id,
            patient_id=patient.id,
            appointment_id=appt.id if appt else None,
            invoice_number=number,
            status=status,
            subtotal=subtotal,
            total=subtotal,
            void_reason="Duplicate entry" if status == "void" else None,
            issued_at=now - timedelta(days=5 - i) if status != "draft" else None,
            voided_at=now - timedelta(days=2) if status == "void" else None,
            created_by_user_id=owner.id,
            financing_status="requested" if i == 5 else None,
        )
        db.add(invoice)
        await db.flush()
        invoices.append(invoice)
        for sort_order, (desc, amount, category) in enumerate(lines):
            db.add(
                InvoiceLineItem(
                    invoice_id=invoice.id,
                    description=desc,
                    category=category,
                    quantity=Decimal("1"),
                    unit_price=amount,
                    amount=amount,
                    sort_order=sort_order,
                    hmo_covered_amount=Decimal("300.00") if i == 1 and sort_order == 0 else None,
                    hmo_claim_reference="MX-CLM-441" if i == 1 and sort_order == 0 else None,
                )
            )
        if payments:
            for method, amount in payments:
                db.add(
                    Payment(
                        invoice_id=invoice.id,
                        clinic_id=clinic.id,
                        method=method,
                        amount=amount,
                        paid_at=now - timedelta(days=4 - i),
                        recorded_by_user_id=reception.id,
                        created_at=now - timedelta(days=4 - i),
                        reference_number="GCASH-88921" if method == "gcash" else None,
                    )
                )

    paid = next(inv for inv in invoices if inv.invoice_number == "INV-0039")
    db.add(
        CreditNote(
            clinic_id=clinic.id,
            invoice_id=paid.id,
            patient_id=paid.patient_id,
            credit_number="CN-0001",
            kind="refund",
            amount=Decimal("150.00"),
            reason="Overcharge on follow-up fee",
            created_by_user_id=admin.id,
            created_at=now - timedelta(days=1),
        )
    )
    partial = next(inv for inv in invoices if inv.invoice_number == "INV-0041")
    db.add(
        CreditNote(
            clinic_id=clinic.id,
            invoice_id=partial.id,
            patient_id=partial.patient_id,
            credit_number="CN-0002",
            kind="adjustment",
            amount=Decimal("50.00"),
            reason="Senior discount applied after issue",
            created_by_user_id=owner.id,
            created_at=now - timedelta(hours=8),
        )
    )

    branch_inv = Invoice(
        clinic_id=branch.id,
        patient_id=branch_patients[1].id,
        invoice_number="BGC-0010",
        status="issued",
        subtotal=Decimal("550.00"),
        total=Decimal("550.00"),
        issued_at=now - timedelta(days=2),
        created_by_user_id=owner.id,
    )
    db.add(branch_inv)
    await db.flush()
    db.add(
        InvoiceLineItem(
            invoice_id=branch_inv.id,
            description="General consultation",
            category="consultation",
            quantity=Decimal("1"),
            unit_price=Decimal("550.00"),
            amount=Decimal("550.00"),
            sort_order=0,
        )
    )
    db.add(
        Payment(
            invoice_id=branch_inv.id,
            clinic_id=branch.id,
            method="cash",
            amount=Decimal("550.00"),
            paid_at=now - timedelta(days=2),
            recorded_by_user_id=reception_b.id,
            created_at=now - timedelta(days=2),
        )
    )
    branch_inv.status = "paid"

    claim_paid = InsuranceClaim(
        clinic_id=clinic.id,
        patient_id=patients[0].id,
        invoice_id=invoices[0].id,
        provider="Maxicare",
        payer_type="hmo",
        member_id="MX-881001",
        claim_reference="MX-2026-1001",
        amount=Decimal("500.00"),
        status="paid",
        notes="Consult covered in full",
        created_by_user_id=reception.id,
        created_at=now - timedelta(days=6),
        updated_at=now - timedelta(days=4),
    )
    claim_draft = InsuranceClaim(
        clinic_id=clinic.id,
        patient_id=patients[4].id,
        invoice_id=partial.id,
        provider="Medicard",
        payer_type="hmo",
        member_id="MD-44219",
        amount=Decimal("800.00"),
        status="draft",
        created_by_user_id=reception.id,
        created_at=now - timedelta(hours=6),
        updated_at=now - timedelta(hours=6),
    )
    claim_submitted = InsuranceClaim(
        clinic_id=clinic.id,
        patient_id=patients[8].id,
        provider="Intellicare",
        payer_type="hmo",
        member_id="IC-77012",
        claim_reference="IC-2026-332",
        amount=Decimal("600.00"),
        status="submitted",
        created_by_user_id=admin.id,
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=1),
    )
    claim_denied = InsuranceClaim(
        clinic_id=clinic.id,
        patient_id=patients[9].id,
        provider="Maxicare",
        payer_type="hmo",
        amount=Decimal("450.00"),
        status="denied",
        notes="Procedure not in benefit schedule",
        created_by_user_id=reception.id,
        created_at=now - timedelta(days=8),
        updated_at=now - timedelta(days=7),
    )
    claim_ph = InsuranceClaim(
        clinic_id=clinic.id,
        patient_id=patients[1].id,
        provider="PhilHealth",
        payer_type="philhealth",
        member_id="PH-19650722",
        claim_reference="PH-CF-8891",
        amount=Decimal("350.00"),
        status="approved",
        created_by_user_id=reception.id,
        created_at=now - timedelta(days=5),
        updated_at=now - timedelta(days=3),
    )
    db.add_all([claim_paid, claim_draft, claim_submitted, claim_denied, claim_ph])
    await db.flush()

    loa_approved = LoaRequest(
        clinic_id=clinic.id,
        patient_id=patients[0].id,
        claim_id=claim_paid.id,
        hmo_name="Maxicare",
        status="approved",
        reference_number="LOA-MX-2201",
        requested_by_user_id=reception.id,
        submitted_at=now - timedelta(days=6),
        decided_at=now - timedelta(days=5),
        decision_notes="Consult approved",
        created_at=now - timedelta(days=6),
        updated_at=now - timedelta(days=5),
    )
    loa_requested = LoaRequest(
        clinic_id=clinic.id,
        patient_id=patients[4].id,
        claim_id=claim_draft.id,
        hmo_name="Medicard",
        status="requested",
        requested_by_user_id=reception.id,
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(hours=5),
    )
    loa_submitted = LoaRequest(
        clinic_id=clinic.id,
        patient_id=patients[8].id,
        claim_id=claim_submitted.id,
        hmo_name="Intellicare",
        status="submitted",
        reference_number="LOA-IC-118",
        requested_by_user_id=reception.id,
        submitted_at=now - timedelta(days=1),
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=1),
    )
    loa_denied = LoaRequest(
        clinic_id=clinic.id,
        patient_id=patients[9].id,
        claim_id=claim_denied.id,
        hmo_name="Maxicare",
        status="denied",
        reference_number="LOA-MX-2290",
        requested_by_user_id=reception.id,
        submitted_at=now - timedelta(days=8),
        decided_at=now - timedelta(days=7),
        decision_notes="Not a covered procedure",
        created_at=now - timedelta(days=8),
        updated_at=now - timedelta(days=7),
    )
    db.add_all([loa_approved, loa_requested, loa_submitted, loa_denied])
    await db.flush()
    claim_paid.loa_request_id = loa_approved.id
    claim_draft.loa_request_id = loa_requested.id
    claim_submitted.loa_request_id = loa_submitted.id
    claim_denied.loa_request_id = loa_denied.id

    db.add_all(
        [
            EligibilityCheck(
                clinic_id=clinic.id,
                patient_id=patients[0].id,
                payer_name="Maxicare",
                payer_type="hmo",
                member_id="MX-881001",
                status="verified",
                verified_amount=Decimal("15000.00"),
                notes="Active principal member",
                checked_by_user_id=reception.id,
                checked_at=now - timedelta(days=3),
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=3),
            ),
            EligibilityCheck(
                clinic_id=clinic.id,
                patient_id=patients[4].id,
                payer_name="Medicard",
                payer_type="hmo",
                member_id="MD-44219",
                status="pending",
                checked_by_user_id=reception.id,
                checked_at=now - timedelta(hours=4),
                created_at=now - timedelta(hours=4),
                updated_at=now - timedelta(hours=4),
            ),
            EligibilityCheck(
                clinic_id=clinic.id,
                patient_id=patients[9].id,
                payer_name="Maxicare",
                payer_type="hmo",
                status="denied",
                notes="Coverage lapsed",
                checked_by_user_id=reception.id,
                checked_at=now - timedelta(days=7),
                created_at=now - timedelta(days=7),
                updated_at=now - timedelta(days=7),
            ),
            EligibilityCheck(
                clinic_id=clinic.id,
                patient_id=patients[1].id,
                payer_name="PhilHealth",
                payer_type="philhealth",
                member_id="PH-19650722",
                status="expired",
                notes="Need updated MDR",
                checked_by_user_id=reception.id,
                checked_at=now - timedelta(days=40),
                created_at=now - timedelta(days=40),
                updated_at=now - timedelta(days=40),
            ),
        ]
    )

    db.add(
        BillingExtractionAttempt(
            clinic_id=clinic.id,
            patient_id=patients[1].id,
            actor_user_id=owner.id,
            source_file_r2_key=f"seed/{clinic.id}/{patients[1].id}/lab-result.pdf",
            extracted_data={
                "suggested_lines": [{"description": "HbA1c", "amount": "850.00"}],
                "confidence": 0.72,
            },
            confirmed=False,
            created_at=now - timedelta(days=8),
        )
    )
    await db.flush()
    return invoices


async def _seed_communications(
    db: AsyncSession,
    *,
    result: SeedResult,
    clinic: Clinic,
    patients: list[Patient],
    appointments: list[Appointment],
    completed_appts: list[Appointment],
    owner: User,
    doctor2: User,
    reception: User,
    admin: User,
    now: datetime,
    today: date,
) -> None:
    upcoming = [a for a in appointments if a.scheduled_start > now and a.clinic_id == clinic.id][:8]
    channels = ("email", "sms", "whatsapp")
    types = ("reminder_24h", "confirmation", "reminder_2h", "reschedule_notice")
    for i, appt in enumerate(upcoming):
        status = "sent" if i < 2 else "pending"
        if i == 4:
            status = "failed"
        if i == 5:
            status = "cancelled"
        db.add(
            Reminder(
                appointment_id=appt.id,
                clinic_id=clinic.id,
                patient_id=appt.patient_id,
                channel=channels[i % 3],
                reminder_type=types[i % len(types)],
                scheduled_send_at=appt.scheduled_start - timedelta(hours=24),
                sent_at=now - timedelta(hours=2) if status == "sent" else None,
                status=status,
                reply_token=secrets.token_urlsafe(16),
                created_at=now - timedelta(days=1),
            )
        )

    recall_specs = [
        (patients[0], "follow_up_date", today - timedelta(days=2), "pending"),
        (patients[1], "chronic_condition_rule", today + timedelta(days=5), "pending"),
        (patients[5], "chronic_condition_rule", today - timedelta(days=10), "contacted"),
        (patients[9], "follow_up_date", today - timedelta(days=30), "booked"),
        (patients[12], "follow_up_date", today + timedelta(days=14), "dismissed"),
        (patients[13], "chronic_condition_rule", today - timedelta(days=4), "pending"),
    ]
    for patient, source, due, status in recall_specs:
        db.add(
            PatientRecall(
                clinic_id=clinic.id,
                patient_id=patient.id,
                source=source,
                due_date=due,
                status=status,
                created_at=now - timedelta(days=20),
            )
        )

    if completed_appts:
        db.add(
            PatientSurveyResponse(
                clinic_id=clinic.id,
                patient_id=completed_appts[0].patient_id,
                visit_id=completed_appts[0].id,
                reply_token=secrets.token_urlsafe(12),
                score=5,
                comment="Staff were on time.",
                sent_at=now - timedelta(days=3),
                responded_at=now - timedelta(days=2),
            )
        )
        if len(completed_appts) > 1:
            db.add(
                PatientSurveyResponse(
                    clinic_id=clinic.id,
                    patient_id=completed_appts[1].patient_id,
                    visit_id=completed_appts[1].id,
                    reply_token=secrets.token_urlsafe(12),
                    sent_at=now - timedelta(days=1),
                )
            )

    maria = next(p for p in patients if p.email == "maria.santos@example.com")
    raw_portal = f"{uuid.uuid4().hex}{uuid.uuid4().hex}"
    db.add(
        PatientPortalToken(
            patient_id=maria.id,
            clinic_id=clinic.id,
            purpose="login",
            token_hash=hash_refresh_token(raw_portal),
            delivery_channel="email",
            expires_at=now + timedelta(days=30),
            created_at=now,
        )
    )
    result.portal_verify_path = f"/patient-portal/{CLINIC_SLUG}/verify?token={raw_portal}"
    result.portal_patient_email = maria.email

    pconv = PatientAssistantConversation(clinic_id=clinic.id, created_at=now - timedelta(hours=5))
    db.add(pconv)
    await db.flush()
    db.add_all(
        [
            PatientAssistantMessage(
                conversation_id=pconv.id,
                role="user",
                content="What are your Saturday hours?",
                created_at=now - timedelta(hours=5),
            ),
            PatientAssistantMessage(
                conversation_id=pconv.id,
                role="assistant",
                content="Saturday hours are 9:00 to 13:00.",
                created_at=now - timedelta(hours=5, minutes=-1),
            ),
        ]
    )

    conv = AiAssistantConversation(clinic_id=clinic.id, user_id=owner.id)
    db.add(conv)
    await db.flush()
    user_msg = AiAssistantMessage(
        conversation_id=conv.id,
        role="user",
        content="Show today's appointments.",
        created_at=now - timedelta(minutes=30),
    )
    asst_msg = AiAssistantMessage(
        conversation_id=conv.id,
        role="assistant",
        content="You have several appointments today. Two patients are in the waiting room.",
        created_at=now - timedelta(minutes=29),
    )
    db.add_all([user_msg, asst_msg])
    await db.flush()
    db.add(
        AiAssistantAction(
            conversation_id=conv.id,
            message_id=asst_msg.id,
            tool_name="list_todays_appointments",
            tier=0,
            status="executed",
            proposal={"date": str(today)},
            result={"count": 8},
            created_at=now - timedelta(minutes=29),
            executed_at=now - timedelta(minutes=29),
        )
    )

    rec_conv = AiAssistantConversation(clinic_id=clinic.id, user_id=reception.id)
    db.add(rec_conv)
    await db.flush()
    rec_user = AiAssistantMessage(
        conversation_id=rec_conv.id,
        role="user",
        content="Book Maria Santos for next Monday 10am.",
        created_at=now - timedelta(hours=2),
    )
    rec_asst = AiAssistantMessage(
        conversation_id=rec_conv.id,
        role="assistant",
        content="I can book that slot. Confirm to create the appointment.",
        created_at=now - timedelta(hours=2, minutes=-1),
    )
    db.add_all([rec_user, rec_asst])
    await db.flush()
    db.add(
        AiAssistantAction(
            conversation_id=rec_conv.id,
            message_id=rec_asst.id,
            tool_name="create_appointment",
            tier=2,
            status="pending",
            proposal={
                "patient_name": "Maria Santos",
                "date": str(today + timedelta(days=7)),
                "time": "10:00",
            },
            created_at=now - timedelta(hours=2, minutes=-1),
        )
    )

    doc_conv = AiAssistantConversation(clinic_id=clinic.id, user_id=doctor2.id)
    db.add(doc_conv)
    await db.flush()
    db.add(
        AiAssistantMessage(
            conversation_id=doc_conv.id,
            role="user",
            content="Who is still waiting?",
            created_at=now - timedelta(minutes=12),
        )
    )

    for days_ago in range(5):
        db.add(
            ClinicAiUsage(
                clinic_id=clinic.id,
                usage_date=today - timedelta(days=days_ago),
                request_count=8 + days_ago * 3,
                token_count=2400 + days_ago * 400,
            )
        )

    notif_specs: list[tuple[str, str, str, list[str], uuid.UUID | None]] = [
        (
            "appointment.public_booked",
            "New public booking",
            "A patient booked from the public link.",
            ["reception", "admin", "owner"],
            None,
        ),
        (
            "visit.arrived",
            "Patient arrived",
            "Maria Santos is in the waiting room.",
            ["doctor", "reception", "owner"],
            None,
        ),
        (
            "appointment.no_show",
            "Marked no-show",
            "A morning appointment was marked no-show.",
            ["reception", "admin", "owner"],
            None,
        ),
        (
            "waitlist.created",
            "Waitlist entry",
            "Grace Tan was added to the waitlist.",
            ["reception", "admin", "owner"],
            None,
        ),
        (
            "invoice.payment_recorded",
            "Payment recorded",
            "A cash payment was recorded.",
            ["owner", "admin", "reception"],
            None,
        ),
        (
            "insurance_claim.denied",
            "Claim denied",
            "A Maxicare claim was denied.",
            ["owner", "admin", "reception"],
            None,
        ),
        (
            "reminder.send_failed",
            "Reminder failed",
            "A 24-hour reminder could not be sent.",
            ["reception", "admin", "owner"],
            None,
        ),
        (
            "prescription.issued",
            "Prescription issued",
            "A prescription was issued.",
            ["doctor", "owner"],
            owner.id,
        ),
        (
            "staff.joined",
            "Staff joined",
            "A new admin signed in.",
            ["owner", "admin"],
            None,
        ),
        (
            "loa_request.status_changed",
            "LOA updated",
            "A Maxicare LOA was approved.",
            ["reception", "admin", "owner"],
            None,
        ),
    ]
    created_notifs: list[Notification] = []
    for i, (ntype, title, body, roles, target) in enumerate(notif_specs):
        row = Notification(
            clinic_id=clinic.id,
            type=ntype,
            title=title,
            body=body,
            entity_type="appointment"
            if "appointment" in ntype or ntype.startswith("visit")
            else None,
            href="/dashboard/waiting-room"
            if ntype == "visit.arrived"
            else "/dashboard/notifications",
            audience_roles=list(roles),
            target_user_id=target,
            actor_user_id=reception.id if i % 2 == 0 else owner.id,
            created_at=now - timedelta(hours=i + 1),
        )
        db.add(row)
        created_notifs.append(row)
    await db.flush()
    db.add(
        NotificationRead(
            notification_id=created_notifs[0].id,
            user_id=owner.id,
            read_at=now - timedelta(minutes=40),
        )
    )
    db.add(
        NotificationRead(
            notification_id=created_notifs[1].id,
            user_id=reception.id,
            read_at=now - timedelta(minutes=15),
        )
    )

    log_entries = [
        (owner.id, "patient.created", "patient", str(patients[0].id), "Registered Maria Santos"),
        (
            reception.id,
            "appointment.created",
            "appointment",
            str(appointments[0].id) if appointments else str(new_uuid()),
            "Booked appointment for today",
        ),
        (reception.id, "visit.status_changed", "appointment", None, "Marked patient arrived"),
        (owner.id, "soap.version_created", "soap_note", None, "Saved SOAP note"),
        (reception.id, "invoice.issued", "invoice", None, "Issued invoice INV-0040"),
        (reception.id, "invoice.payment_recorded", "invoice", None, "Recorded cash payment"),
        (owner.id, "prescription.issued", "prescription", None, "Issued prescription"),
        (owner.id, "document.issued", "document", None, "Issued referral letter"),
        (reception.id, "recall.status_changed", "patient_recall", None, "Updated recall status"),
        (admin.id, "clinic.updated", "clinic", str(clinic.id), "Updated clinic profile"),
        (
            reception.id,
            "waitlist.created",
            "waitlist",
            None,
            "Patient added to cancellation waitlist",
        ),
        (
            reception.id,
            "eligibility.checked",
            "eligibility_check",
            None,
            "Verified Maxicare eligibility",
        ),
        (owner.id, "clinical_order.created", "clinical_order", None, "Ordered HbA1c"),
        ("ai", "assistant.action_executed", "appointment", None, "Listed today's appointments"),
        (None, "reminder.sent", "reminder", None, "Sent 24-hour reminder"),
    ]
    for i, (actor, action, target_type, target_id, summary) in enumerate(log_entries):
        actor_type = "user"
        actor_id: uuid.UUID | None
        if actor == "ai":
            actor_type = "ai_assistant"
            actor_id = owner.id
        elif actor is None:
            actor_type = "system"
            actor_id = None
        else:
            actor_id = actor  # type: ignore[assignment]
        db.add(
            ActivityLog(
                clinic_id=clinic.id,
                actor_user_id=actor_id,
                actor_type=actor_type,
                action=action,
                target_type=target_type,
                target_id=target_id or str(new_uuid()),
                summary=summary,
                created_at=now - timedelta(hours=i * 2),
            )
        )
    await db.flush()


async def _seed_platform(
    db: AsyncSession,
    *,
    org: Organization,
    clinic: Clinic,
    branch: Clinic,
    platform: User,
    now: datetime,
) -> None:
    existing = await db.get(PlatformFeatureFlag, "ai_assistant")
    if existing is None:
        db.add(PlatformFeatureFlag(key="ai_assistant", enabled=True, updated_at=now))
    else:
        existing.enabled = True
        existing.updated_at = now

    db.add_all(
        [
            PlatformAuditLog(
                actor_user_id=platform.id,
                action="tenant.activated",
                target_type="organization",
                target_id=str(org.id),
                summary="Activated Makati Family Group enrollment",
                created_at=now - timedelta(days=40),
            ),
            PlatformAuditLog(
                actor_user_id=platform.id,
                action="clinic.plan_updated",
                target_type="clinic",
                target_id=str(clinic.id),
                summary="Set clinic plan to Clinic",
                created_at=now - timedelta(days=39),
            ),
            PlatformAuditLog(
                actor_user_id=platform.id,
                action="clinic.enrolled",
                target_type="clinic",
                target_id=str(branch.id),
                summary="Activated BGC branch enrollment",
                created_at=now - timedelta(days=40),
            ),
        ]
    )
    await db.flush()
