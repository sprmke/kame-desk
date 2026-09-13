import csv
import io
import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Appointment,
    DoctorProfile,
    Invoice,
    InvoiceLineItem,
    Patient,
    Payment,
    SoapNote,
    User,
)

MANILA = ZoneInfo("Asia/Manila")
GROUP_BY_VALUES = ("day", "week", "month", "doctor", "service_type")


def _money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


async def _doctor_names(db: AsyncSession, doctor_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not doctor_ids:
        return {}
    result = await db.execute(
        select(DoctorProfile, User)
        .join(User, User.id == DoctorProfile.user_id)
        .where(DoctorProfile.id.in_(doctor_ids))
    )
    return {profile.id: user.full_name for profile, user in result.all()}


def parse_report_range(from_date: date, to_date: date) -> tuple[datetime, datetime]:
    start_local = datetime.combine(from_date, time.min, tzinfo=MANILA)
    end_local = datetime.combine(to_date, time.max, tzinfo=MANILA)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def _period_expr(column, group_by: str):
    if group_by == "week":
        return func.date_trunc("week", column)
    if group_by == "month":
        return func.date_trunc("month", column)
    return func.date_trunc("day", column)


async def get_appointment_report(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    from_date: date,
    to_date: date,
    group_by: str = "day",
    doctor_id: uuid.UUID | None = None,
) -> dict:
    start, end = parse_report_range(from_date, to_date)
    period = _period_expr(Appointment.scheduled_start, group_by)

    booked = func.count().filter(
        Appointment.appointment_status.notin_(("Cancelled", "Rescheduled"))
    )
    completed = func.count().filter(Appointment.current_visit_status == "Completed")
    no_show = func.count().filter(Appointment.appointment_status == "No Show")
    cancelled = func.count().filter(Appointment.appointment_status == "Cancelled")

    q = (
        select(
            period.label("period"),
            booked.label("booked"),
            completed.label("completed"),
            no_show.label("no_show"),
            cancelled.label("cancelled"),
        )
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.scheduled_start >= start,
            Appointment.scheduled_start <= end,
        )
        .group_by(period)
        .order_by(period)
    )
    if group_by == "doctor":
        q = (
            select(
                Appointment.doctor_id.label("doctor_id"),
                booked.label("booked"),
                completed.label("completed"),
                no_show.label("no_show"),
                cancelled.label("cancelled"),
            )
            .where(
                Appointment.clinic_id == clinic_id,
                Appointment.scheduled_start >= start,
                Appointment.scheduled_start <= end,
            )
            .group_by(Appointment.doctor_id)
            .order_by(Appointment.doctor_id)
        )
    if doctor_id is not None:
        q = q.where(Appointment.doctor_id == doctor_id)

    rows = await db.execute(q)
    series = []
    for row in rows.all():
        item = {
            "booked": int(row.booked),
            "completed": int(row.completed),
            "no_show": int(row.no_show),
            "cancelled": int(row.cancelled),
        }
        if group_by == "doctor":
            item["doctor_id"] = str(row.doctor_id)
        else:
            item["period"] = row.period.date().isoformat() if row.period else None
        series.append(item)
    if group_by == "doctor":
        names = await _doctor_names(
            db, [uuid.UUID(item["doctor_id"]) for item in series if item.get("doctor_id")]
        )
        for item in series:
            did = uuid.UUID(item["doctor_id"])
            item["doctor_name"] = names.get(did) or "Doctor"
    return {"series": series, "from_date": from_date.isoformat(), "to_date": to_date.isoformat()}


async def get_revenue_totals(db: AsyncSession, clinic_id: uuid.UUID) -> dict[str, str]:
    now = datetime.now(MANILA)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)
    start_of_week = (
        (now - timedelta(days=now.weekday()))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .astimezone(UTC)
    )
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)

    async def _sum_since(since: datetime) -> str:
        result = await db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.clinic_id == clinic_id,
                Payment.paid_at >= since,
            )
        )
        return str(_money(result.scalar_one()))

    return {
        "today": await _sum_since(start_of_day),
        "week": await _sum_since(start_of_week),
        "month": await _sum_since(start_of_month),
    }


async def get_revenue_report(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    from_date: date,
    to_date: date,
    group_by: str = "day",
    doctor_id: uuid.UUID | None = None,
) -> dict:
    start, end = parse_report_range(from_date, to_date)
    totals = await get_revenue_totals(db, clinic_id)

    if group_by == "service_type":
        q = (
            select(
                InvoiceLineItem.category.label("service_type"),
                func.coalesce(func.sum(InvoiceLineItem.amount), 0).label("amount"),
            )
            .join(Invoice, Invoice.id == InvoiceLineItem.invoice_id)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.in_(("issued", "partially_paid", "paid")),
                Invoice.issued_at >= start,
                Invoice.issued_at <= end,
            )
            .group_by(InvoiceLineItem.category)
            .order_by(InvoiceLineItem.category)
        )
        rows = await db.execute(q)
        series = [
            {"service_type": r.service_type, "amount": str(_money(r.amount))} for r in rows.all()
        ]
        return {
            "series": series,
            "totals": totals,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        }

    if group_by == "doctor":
        q = (
            select(
                Appointment.doctor_id.label("doctor_id"),
                func.coalesce(func.sum(Payment.amount), 0).label("amount"),
            )
            .join(Invoice, Invoice.id == Payment.invoice_id)
            .join(Appointment, Appointment.id == Invoice.appointment_id)
            .where(
                Payment.clinic_id == clinic_id,
                Payment.paid_at >= start,
                Payment.paid_at <= end,
            )
            .group_by(Appointment.doctor_id)
            .order_by(Appointment.doctor_id)
        )
        if doctor_id is not None:
            q = q.where(Appointment.doctor_id == doctor_id)
        rows = await db.execute(q)
        series = [
            {"doctor_id": str(r.doctor_id), "amount": str(_money(r.amount))} for r in rows.all()
        ]
        names = await _doctor_names(
            db, [uuid.UUID(item["doctor_id"]) for item in series if item.get("doctor_id")]
        )
        for item in series:
            did = uuid.UUID(item["doctor_id"])
            item["doctor_name"] = names.get(did) or "Doctor"
        return {
            "series": series,
            "totals": totals,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        }

    period = _period_expr(Payment.paid_at, group_by)
    q = (
        select(
            period.label("period"),
            func.coalesce(func.sum(Payment.amount), 0).label("amount"),
        )
        .where(
            Payment.clinic_id == clinic_id,
            Payment.paid_at >= start,
            Payment.paid_at <= end,
        )
        .group_by(period)
        .order_by(period)
    )
    rows = await db.execute(q)
    series = [
        {
            "period": r.period.date().isoformat() if r.period else None,
            "amount": str(_money(r.amount)),
        }
        for r in rows.all()
    ]
    return {
        "series": series,
        "totals": totals,
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
    }


async def get_patient_growth_report(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    from_date: date,
    to_date: date,
    group_by: str = "month",
) -> dict:
    start, end = parse_report_range(from_date, to_date)
    period = _period_expr(Patient.created_at, group_by)

    new_q = (
        select(period.label("period"), func.count().label("new_patients"))
        .where(
            Patient.clinic_id == clinic_id,
            Patient.created_at >= start,
            Patient.created_at <= end,
            Patient.is_archived.is_(False),
        )
        .group_by(period)
        .order_by(period)
    )
    new_rows = {
        r.period.date().isoformat(): int(r.new_patients) for r in (await db.execute(new_q)).all()
    }

    appt_period = _period_expr(Appointment.scheduled_start, group_by)
    returning_q = (
        select(
            appt_period.label("period"),
            func.count(func.distinct(Appointment.patient_id)).label("returning_patients"),
        )
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.scheduled_start >= start,
            Appointment.scheduled_start <= end,
            Appointment.appointment_status.notin_(("Cancelled", "Rescheduled")),
            Appointment.patient_id.in_(
                select(Patient.id).where(
                    Patient.clinic_id == clinic_id,
                    Patient.created_at < start,
                )
            ),
        )
        .group_by(appt_period)
        .order_by(appt_period)
    )
    returning_rows = {
        r.period.date().isoformat(): int(r.returning_patients)
        for r in (await db.execute(returning_q)).all()
    }

    periods = sorted(set(new_rows) | set(returning_rows))
    series = [
        {
            "period": p,
            "new_patients": new_rows.get(p, 0),
            "returning_patients": returning_rows.get(p, 0),
        }
        for p in periods
    ]
    return {"series": series, "from_date": from_date.isoformat(), "to_date": to_date.isoformat()}


async def get_top_diagnoses_report(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    from_date: date,
    to_date: date,
    limit: int = 20,
) -> dict:
    start, end = parse_report_range(from_date, to_date)
    latest_signed = (
        select(
            SoapNote.appointment_id,
            func.max(SoapNote.version_number).label("max_version"),
        )
        .where(
            SoapNote.clinic_id == clinic_id,
            SoapNote.signed_at.isnot(None),
            SoapNote.signed_at >= start,
            SoapNote.signed_at <= end,
        )
        .group_by(SoapNote.appointment_id)
        .subquery()
    )
    label = func.coalesce(SoapNote.diagnosis_primary, "Unspecified")
    q = (
        select(label.label("diagnosis"), func.count().label("visit_count"))
        .join(
            latest_signed,
            (SoapNote.appointment_id == latest_signed.c.appointment_id)
            & (SoapNote.version_number == latest_signed.c.max_version),
        )
        .where(
            SoapNote.clinic_id == clinic_id,
            SoapNote.signed_at.isnot(None),
        )
        .group_by(label)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = await db.execute(q)
    series = [{"diagnosis": r.diagnosis, "visit_count": int(r.visit_count)} for r in rows.all()]
    return {
        "series": series,
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
    }


def report_to_csv(report_key: str, payload: dict) -> str:
    output = io.StringIO()
    series = payload.get("series") or []
    if not series:
        writer = csv.writer(output)
        writer.writerow(["no_data"])
        return output.getvalue()

    writer = csv.DictWriter(output, fieldnames=list(series[0].keys()))
    writer.writeheader()
    writer.writerows(series)
    return output.getvalue()
