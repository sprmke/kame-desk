from datetime import date

from pydantic import BaseModel, Field


class SoapDraft(BaseModel):
    subjective: str = Field(description="Subjective section")
    objective: str = Field(description="Objective section including vitals")
    assessment: str = Field(description="Assessment / diagnosis narrative")
    plan: str = Field(description="Treatment plan")
    diagnosis_primary: str | None = Field(default=None, description="Primary diagnosis label")
    diagnosis_secondary: list[str] | None = Field(default=None)
    icd10_codes: list[str] | None = Field(default=None)
    follow_up_date: date | None = Field(default=None, description="Suggested follow-up date")


class SoapDraftContext(BaseModel):
    vitals_summary: str | None = None
    chronic_conditions: list[str] = Field(default_factory=list)
