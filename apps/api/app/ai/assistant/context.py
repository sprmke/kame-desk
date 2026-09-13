import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel


class PageContext(BaseModel):
    route: str | None = None
    patient_id: uuid.UUID | None = None
    appointment_id: uuid.UUID | None = None
    visit_id: uuid.UUID | None = None


class AttachedContextItem(BaseModel):
    type: Literal["patient", "appointment", "invoice"]
    id: uuid.UUID
    label: str | None = None


@dataclass
class ResolvedContext:
    page: PageContext = field(default_factory=PageContext)
    attached: list[AttachedContextItem] = field(default_factory=list)

    def allowed_patient_ids(self) -> set[uuid.UUID]:
        ids: set[uuid.UUID] = set()
        if self.page.patient_id:
            ids.add(self.page.patient_id)
        for item in self.attached:
            if item.type == "patient":
                ids.add(item.id)
        return ids

    def allowed_appointment_ids(self) -> set[uuid.UUID]:
        ids: set[uuid.UUID] = set()
        if self.page.appointment_id:
            ids.add(self.page.appointment_id)
        for item in self.attached:
            if item.type == "appointment":
                ids.add(item.id)
        return ids

    def allowed_invoice_ids(self) -> set[uuid.UUID]:
        return {item.id for item in self.attached if item.type == "invoice"}


def resolve_tool_args(
    explicit_args: dict[str, Any],
    ctx: ResolvedContext,
    field_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Merge explicit args with attached/page context (explicit wins)."""
    out = dict(explicit_args)
    mapping = field_map or {
        "patient_id": "patient_id",
        "appointment_id": "appointment_id",
        "invoice_id": "invoice_id",
    }

    for arg_key, ctx_key in mapping.items():
        if out.get(arg_key):
            continue
        if ctx_key == "patient_id" and ctx.page.patient_id:
            out[arg_key] = str(ctx.page.patient_id)
        elif ctx_key == "appointment_id" and ctx.page.appointment_id:
            out[arg_key] = str(ctx.page.appointment_id)

    for item in ctx.attached:
        if item.type == "patient" and not out.get("patient_id"):
            out["patient_id"] = str(item.id)
        if item.type == "appointment" and not out.get("appointment_id"):
            out["appointment_id"] = str(item.id)
        if item.type == "invoice" and not out.get("invoice_id"):
            out["invoice_id"] = str(item.id)

    return out


def is_cross_scope(tool_args: dict[str, Any], ctx: ResolvedContext) -> bool:
    """True when acting on IDs outside page + pinned context."""
    has_scope = bool(
        ctx.page.patient_id or ctx.page.appointment_id or ctx.page.visit_id or ctx.attached
    )
    if not has_scope:
        return False

    patient_ids = ctx.allowed_patient_ids()
    appointment_ids = ctx.allowed_appointment_ids()
    invoice_ids = ctx.allowed_invoice_ids()

    pid = tool_args.get("patient_id")
    if pid and patient_ids and uuid.UUID(str(pid)) not in patient_ids:
        return True

    aid = tool_args.get("appointment_id")
    if aid and appointment_ids and uuid.UUID(str(aid)) not in appointment_ids:
        return True

    iid = tool_args.get("invoice_id")
    if iid and invoice_ids and uuid.UUID(str(iid)) not in invoice_ids:
        return True

    return False
