import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, new_uuid

TOOTH_CONDITIONS = (
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
TOOTH_SURFACES = ("mesial", "distal", "occlusal", "buccal", "lingual", "incisal")
TOOTH_ENTRY_STATUSES = ("existing", "planned", "completed")


class ToothChartEntry(Base):
    """Append-only per-tooth/per-surface chart entries (FDI numbering, adult
    permanent dentition 11-48). Never UPDATE a prior entry's condition — a new
    finding is always a new row, so `noted_at` order reconstructs progression
    (e.g. caries -> filled -> crown) for the same tooth/surface over time."""

    __tablename__ = "tooth_chart_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    # No standalone index: covered by the composite ix_tooth_chart_entries_patient_id_noted_at
    # (patient_id, noted_at DESC), which also serves the list_entries query order.
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True
    )
    soap_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("soap_notes.id"), nullable=True
    )
    tooth_number: Mapped[int] = mapped_column(Integer, nullable=False)
    surface: Mapped[str | None] = mapped_column(String(16), nullable=True)
    condition: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="existing", nullable=False)
    procedure_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    invoice_line_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_line_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    noted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
