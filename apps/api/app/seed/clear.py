"""Tear down synthetic demo clinics so seed can be re-run."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AccountToken,
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
    Prescription,
    PrescriptionItem,
    PushSubscription,
    RefreshToken,
    Reminder,
    Room,
    ServiceFee,
    SoapNote,
    SoapNoteEmbedding,
    StaffInvitation,
    User,
    VisitStatusEvent,
    VisitSummary,
)
from app.seed.constants import DEMO_CLINIC_SLUGS, DEMO_EMAILS, ORG_SLUG


@asynccontextmanager
async def _local_dev_trigger_bypass(db: AsyncSession) -> AsyncIterator[None]:
    """Disable row triggers so local seed teardown can clear append-only tables."""
    await db.execute(text("SET LOCAL session_replication_role = replica"))
    try:
        yield
    finally:
        await db.execute(text("SET LOCAL session_replication_role = DEFAULT"))


async def demo_data_exists(db: AsyncSession) -> bool:
    clinic_id = await db.scalar(select(Clinic.id).where(Clinic.slug.in_(DEMO_CLINIC_SLUGS)))
    if clinic_id is not None:
        return True
    org_id = await db.scalar(select(Organization.id).where(Organization.slug == ORG_SLUG))
    return org_id is not None


async def clear_demo_data(db: AsyncSession) -> None:
    clinic_ids = list(
        (await db.scalars(select(Clinic.id).where(Clinic.slug.in_(DEMO_CLINIC_SLUGS)))).all()
    )
    org_id = await db.scalar(select(Organization.id).where(Organization.slug == ORG_SLUG))
    if not clinic_ids and org_id is None:
        return

    async with _local_dev_trigger_bypass(db):
        for clinic_id in clinic_ids:
            await _clear_clinic_rows(db, clinic_id)
        if org_id is not None:
            await db.execute(
                delete(OrganizationEnrolledClinic).where(
                    OrganizationEnrolledClinic.organization_id == org_id
                )
            )
            await db.execute(
                delete(OrganizationSubscription).where(
                    OrganizationSubscription.organization_id == org_id
                )
            )
        if clinic_ids:
            await db.execute(delete(Clinic).where(Clinic.id.in_(clinic_ids)))
        if org_id is not None:
            await db.execute(delete(Organization).where(Organization.id == org_id))
        await _clear_demo_users(db)
    await db.commit()


async def _ids(db: AsyncSession, stmt) -> Sequence[uuid.UUID]:
    return list((await db.scalars(stmt)).all())


async def _clear_clinic_rows(db: AsyncSession, clinic_id: uuid.UUID) -> None:
    notif_ids = await _ids(db, select(Notification.id).where(Notification.clinic_id == clinic_id))
    if notif_ids:
        await db.execute(
            delete(NotificationRead).where(NotificationRead.notification_id.in_(notif_ids))
        )
        await db.execute(delete(Notification).where(Notification.id.in_(notif_ids)))
    await db.execute(delete(PushSubscription).where(PushSubscription.clinic_id == clinic_id))

    conv_ids = await _ids(
        db,
        select(PatientAssistantConversation.id).where(
            PatientAssistantConversation.clinic_id == clinic_id
        ),
    )
    if conv_ids:
        await db.execute(
            delete(PatientAssistantMessage).where(
                PatientAssistantMessage.conversation_id.in_(conv_ids)
            )
        )
        await db.execute(
            delete(PatientAssistantConversation).where(
                PatientAssistantConversation.id.in_(conv_ids)
            )
        )

    ai_ids = await _ids(
        db,
        select(AiAssistantConversation.id).where(AiAssistantConversation.clinic_id == clinic_id),
    )
    if ai_ids:
        await db.execute(
            delete(AiAssistantAction).where(AiAssistantAction.conversation_id.in_(ai_ids))
        )
        await db.execute(
            delete(AiAssistantMessage).where(AiAssistantMessage.conversation_id.in_(ai_ids))
        )
        await db.execute(
            delete(AiAssistantConversation).where(AiAssistantConversation.id.in_(ai_ids))
        )

    await db.execute(delete(Reminder).where(Reminder.clinic_id == clinic_id))
    await db.execute(delete(PatientRecall).where(PatientRecall.clinic_id == clinic_id))
    await db.execute(
        delete(PatientSurveyResponse).where(PatientSurveyResponse.clinic_id == clinic_id)
    )
    await db.execute(delete(PatientPortalToken).where(PatientPortalToken.clinic_id == clinic_id))
    await db.execute(delete(VisitSummary).where(VisitSummary.clinic_id == clinic_id))
    await db.execute(delete(VisitStatusEvent).where(VisitStatusEvent.clinic_id == clinic_id))
    await db.execute(
        delete(ConsultationRecording).where(ConsultationRecording.clinic_id == clinic_id)
    )
    await db.execute(delete(AppointmentWaitlist).where(AppointmentWaitlist.clinic_id == clinic_id))
    await db.execute(delete(ClinicalOrder).where(ClinicalOrder.clinic_id == clinic_id))
    await db.execute(
        delete(BillingExtractionAttempt).where(BillingExtractionAttempt.clinic_id == clinic_id)
    )
    await db.execute(delete(ActivityLog).where(ActivityLog.clinic_id == clinic_id))
    await db.execute(delete(ClinicAiUsage).where(ClinicAiUsage.clinic_id == clinic_id))

    await db.execute(delete(LoaRequest).where(LoaRequest.clinic_id == clinic_id))
    await db.execute(delete(InsuranceClaim).where(InsuranceClaim.clinic_id == clinic_id))
    await db.execute(delete(EligibilityCheck).where(EligibilityCheck.clinic_id == clinic_id))
    await db.execute(delete(Payer).where(Payer.clinic_id == clinic_id))
    await db.execute(delete(PatientMembership).where(PatientMembership.clinic_id == clinic_id))
    await db.execute(delete(MembershipPlan).where(MembershipPlan.clinic_id == clinic_id))
    await db.execute(delete(CreditNote).where(CreditNote.clinic_id == clinic_id))

    invoice_ids = await _ids(db, select(Invoice.id).where(Invoice.clinic_id == clinic_id))
    if invoice_ids:
        await db.execute(delete(Payment).where(Payment.invoice_id.in_(invoice_ids)))
        await db.execute(delete(InvoiceLineItem).where(InvoiceLineItem.invoice_id.in_(invoice_ids)))
        await db.execute(delete(Invoice).where(Invoice.id.in_(invoice_ids)))

    rx_ids = await _ids(db, select(Prescription.id).where(Prescription.clinic_id == clinic_id))
    if rx_ids:
        await db.execute(
            delete(PrescriptionItem).where(PrescriptionItem.prescription_id.in_(rx_ids))
        )
        await db.execute(delete(Prescription).where(Prescription.id.in_(rx_ids)))

    await db.execute(delete(GeneratedDocument).where(GeneratedDocument.clinic_id == clinic_id))
    await db.execute(delete(PatientFile).where(PatientFile.clinic_id == clinic_id))
    await db.execute(delete(PatientVital).where(PatientVital.clinic_id == clinic_id))
    await db.execute(delete(SoapNoteEmbedding).where(SoapNoteEmbedding.clinic_id == clinic_id))
    await db.execute(delete(SoapNote).where(SoapNote.clinic_id == clinic_id))
    await db.execute(delete(Appointment).where(Appointment.clinic_id == clinic_id))
    await db.execute(delete(AppointmentSeries).where(AppointmentSeries.clinic_id == clinic_id))
    await db.execute(delete(PatientMedicalInfo).where(PatientMedicalInfo.clinic_id == clinic_id))
    await db.execute(delete(Patient).where(Patient.clinic_id == clinic_id))
    await db.execute(delete(DocumentTemplate).where(DocumentTemplate.clinic_id == clinic_id))
    await db.execute(delete(ServiceFee).where(ServiceFee.clinic_id == clinic_id))
    await db.execute(delete(StaffInvitation).where(StaffInvitation.clinic_id == clinic_id))
    await db.execute(delete(DoctorProfile).where(DoctorProfile.clinic_id == clinic_id))
    await db.execute(delete(Room).where(Room.clinic_id == clinic_id))
    await db.execute(delete(ClinicMembership).where(ClinicMembership.clinic_id == clinic_id))


async def _clear_demo_users(db: AsyncSession) -> None:
    user_ids = await _ids(db, select(User.id).where(User.email.in_(DEMO_EMAILS)))
    if not user_ids:
        return
    await db.execute(delete(PlatformAuditLog).where(PlatformAuditLog.actor_user_id.in_(user_ids)))
    await db.execute(delete(AccountToken).where(AccountToken.user_id.in_(user_ids)))
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id.in_(user_ids)))
    await db.execute(delete(ClinicMembership).where(ClinicMembership.user_id.in_(user_ids)))
    await db.execute(delete(User).where(User.id.in_(user_ids)))
