import uuid

from app.core.realtime_bus import publish_clinic_event


async def broadcast_appointment_event(
    clinic_id: uuid.UUID,
    event: str,
    appointment_id: uuid.UUID,
) -> None:
    await publish_clinic_event(
        clinic_id,
        event,
        {"appointment_id": str(appointment_id)},
    )
