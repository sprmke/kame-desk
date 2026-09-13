import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PatientPortalLoginRequest(BaseModel):
    clinic_slug: str = Field(min_length=1, max_length=255)
    identifier: str = Field(min_length=1, max_length=320)


class PatientPortalLoginRequestResponse(BaseModel):
    message: str = (
        "If that matches a record on file, we sent a login link. Check your email or phone."
    )


class PatientPortalVerifyRequest(BaseModel):
    token: str = Field(min_length=1)


class PatientPortalSessionRead(BaseModel):
    access_token: str
    expires_in_minutes: int
    patient_id: uuid.UUID
    clinic_id: uuid.UUID


class PatientPortalMeRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    clinic_name: str
    full_name: str
    email: str | None
    contact_number: str | None

    model_config = {"from_attributes": True}


class PatientPortalVisitRead(BaseModel):
    id: uuid.UUID
    scheduled_start: datetime
    doctor_name: str
    reason_for_visit: str | None
    appointment_status: str
    current_visit_status: str | None


class PatientPortalVitalRead(BaseModel):
    recorded_at: datetime
    height_cm: Decimal | None
    weight_kg: Decimal | None
    bmi: Decimal | None
    blood_pressure: str | None
    temperature_c: Decimal | None
    heart_rate: int | None
    respiratory_rate: int | None
    spo2: int | None

    model_config = {"from_attributes": True}


class PatientPortalDiagnosisRead(BaseModel):
    visit_date: datetime
    doctor_name: str
    diagnosis_primary: str | None
    diagnosis_secondary: list[str] | None
    icd10_codes: list[str] | None
    follow_up_date: date | None


class PatientPortalChartSummaryRead(BaseModel):
    diagnoses: list[PatientPortalDiagnosisRead]
    vitals: list[PatientPortalVitalRead]


class PatientPortalInvoiceRead(BaseModel):
    id: uuid.UUID
    invoice_number: str | None
    status: str
    total: Decimal
    amount_paid: Decimal
    balance: Decimal
    issued_at: datetime | None


class PatientPortalInvoiceListResponse(BaseModel):
    items: list[PatientPortalInvoiceRead]
    total_balance: Decimal


class PatientPortalDocumentRead(BaseModel):
    id: uuid.UUID
    file_type: str
    description: str | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class PatientPortalDocumentDownloadRead(BaseModel):
    download_url: str
    expires_in_seconds: int = 300
