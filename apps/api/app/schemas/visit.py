import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

VisitStatus = Literal["Arrived", "In Consultation", "Completed"]


class VisitStatusUpdate(BaseModel):
    visit_status: VisitStatus


class WaitingRoomEntry(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str | None = None
    doctor_id: uuid.UUID
    doctor_name: str | None = None
    scheduled_start: datetime
    scheduled_end: datetime
    appointment_status: str
    current_visit_status: str | None = None
    reason_for_visit: str | None = None

    model_config = {"from_attributes": True}


class WaitingRoomResponse(BaseModel):
    items: list[WaitingRoomEntry]
    date: str
