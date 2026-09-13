from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.realtime_bus import start_realtime_subscriber, stop_realtime_subscriber
from app.routers import (
    activity_log,
    appointment_series,
    appointments,
    assistant,
    auth,
    billing_assist,
    claims,
    clinical_orders,
    clinics,
    doctors,
    documents,
    eligibility_checks,
    health,
    invitations,
    invoices,
    loa_requests,
    membership_plans,
    notifications,
    organizations,
    patient_assistant,
    patient_portal,
    patients,
    payers,
    plans,
    platform,
    prescriptions,
    public_booking,
    public_documents,
    public_nps,
    public_reminders,
    recalls,
    recordings,
    reminders,
    reports,
    soap,
    tooth_chart,
    visit_summaries,
    whatsapp_webhook,
    ws,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_realtime_subscriber()
    yield
    await stop_realtime_subscriber()


def create_app() -> FastAPI:
    app = FastAPI(title="DoctorDesk API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(activity_log.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(billing_assist.router, prefix="/api/v1")
    app.include_router(clinics.router, prefix="/api/v1")
    app.include_router(claims.router, prefix="/api/v1")
    app.include_router(eligibility_checks.router, prefix="/api/v1")
    app.include_router(loa_requests.router, prefix="/api/v1")
    app.include_router(payers.router, prefix="/api/v1")
    app.include_router(clinical_orders.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(doctors.router, prefix="/api/v1")
    app.include_router(invitations.router, prefix="/api/v1")
    app.include_router(patients.router, prefix="/api/v1")
    app.include_router(platform.router, prefix="/api/v1")
    app.include_router(plans.router, prefix="/api/v1")
    app.include_router(invoices.router, prefix="/api/v1")
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(organizations.router, prefix="/api/v1")
    app.include_router(prescriptions.router, prefix="/api/v1")
    app.include_router(appointments.router, prefix="/api/v1")
    app.include_router(visit_summaries.router, prefix="/api/v1")
    app.include_router(assistant.router, prefix="/api/v1")
    app.include_router(soap.router, prefix="/api/v1")
    app.include_router(appointment_series.router, prefix="/api/v1")
    app.include_router(public_booking.router, prefix="/api/v1")
    app.include_router(patient_assistant.router, prefix="/api/v1")
    app.include_router(patient_portal.router, prefix="/api/v1")
    app.include_router(public_reminders.router, prefix="/api/v1")
    app.include_router(public_nps.router, prefix="/api/v1")
    app.include_router(public_documents.router, prefix="/api/v1")
    app.include_router(membership_plans.router, prefix="/api/v1")
    app.include_router(recalls.router, prefix="/api/v1")
    app.include_router(reminders.router, prefix="/api/v1")
    app.include_router(whatsapp_webhook.router, prefix="/api/v1")
    app.include_router(recordings.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    app.include_router(tooth_chart.router, prefix="/api/v1")
    app.include_router(ws.router)
    return app


app = create_app()
