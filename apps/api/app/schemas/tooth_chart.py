import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

# FDI two-digit notation, adult permanent dentition only (quadrants 1-4, teeth 1-8).
# Primary/deciduous dentition (quadrants 5-8) is explicitly out of scope for this phase.
VALID_TOOTH_NUMBERS = frozenset(
    quadrant * 10 + tooth for quadrant in (1, 2, 3, 4) for tooth in range(1, 9)
)

CONDITIONS = (
    "sound",
    "caries",
    "filled",
    "missing",
    "crown",
    "root_canal",
    "extraction_planned",
    "impacted",
    "fractured",
)
SURFACES = ("mesial", "distal", "occlusal", "buccal", "lingual", "incisal")
STATUSES = ("existing", "planned", "completed")


class ToothChartEntryCreate(BaseModel):
    appointment_id: uuid.UUID | None = None
    soap_note_id: uuid.UUID | None = None
    tooth_number: int
    surface: str | None = Field(default=None, pattern="^(" + "|".join(SURFACES) + ")$")
    condition: str = Field(pattern="^(" + "|".join(CONDITIONS) + ")$")
    status: str = Field(default="existing", pattern="^(" + "|".join(STATUSES) + ")$")
    procedure_code: str | None = Field(default=None, max_length=32)

    @field_validator("tooth_number")
    @classmethod
    def _valid_fdi_tooth(cls, v: int) -> int:
        if v not in VALID_TOOTH_NUMBERS:
            raise ValueError(
                "tooth_number must be a valid FDI adult tooth code (11-18, 21-28, 31-38, 41-48)"
            )
        return v


class ToothChartEntryRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    appointment_id: uuid.UUID | None
    soap_note_id: uuid.UUID | None
    tooth_number: int
    surface: str | None
    condition: str
    status: str
    procedure_code: str | None
    invoice_line_item_id: uuid.UUID | None
    noted_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ToothChartAddToInvoiceRequest(BaseModel):
    description: str = Field(min_length=1, max_length=512)
    amount: Decimal = Field(ge=0)
    appointment_id: uuid.UUID | None = None


class ToothChartAddToInvoiceResponse(BaseModel):
    entry: ToothChartEntryRead
    invoice_id: uuid.UUID
