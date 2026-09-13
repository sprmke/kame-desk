"""Clinic-scoped permission strings — single source for session + nav gating."""

from __future__ import annotations

from typing import Literal

from app.models import Clinic, ClinicMembership

Role = Literal["owner", "admin", "doctor", "reception"]

# Navigation
TODAY_VIEW = "today:view"
SCHEDULE_VIEW = "schedule:view"
WAITING_ROOM_VIEW = "waiting_room:view"
PATIENTS_VIEW = "patients:view"
PATIENTS_CHART_SEARCH = "patients:chart_search"
BILLING_VIEW = "billing:view"
OUTREACH_VIEW = "outreach:view"
DOCUMENTS_VIEW = "documents:view"
INSIGHTS_VIEW = "insights:view"

# Actions
SCHEDULE_WRITE = "schedule:write"
PATIENTS_WRITE = "patients:write"
PATIENTS_MERGE = "patients:merge"
BILLING_WRITE = "billing:write"
BILLING_VOID = "billing:void"
OUTREACH_MANAGE = "outreach:manage"
DOCUMENTS_WRITE = "documents:write"
REPORTS_VIEW = "reports:view"
AUDIT_LOG_VIEW = "audit_log:view"
SOAP_READ = "soap:read"
SOAP_WRITE = "soap:write"
PRESCRIPTIONS_WRITE = "prescriptions:write"
CHART_SEARCH = "chart_search:use"

# Settings
SETTINGS_ACCOUNT = "settings:account"
SETTINGS_DOCTOR = "settings:doctor"
SETTINGS_CLINIC = "settings:clinic"
SETTINGS_TEAM = "settings:team"
SETTINGS_SERVICES = "settings:services"
SETTINGS_NOTIFICATIONS = "settings:notifications"
SETTINGS_ASSISTANT = "settings:assistant"
SETTINGS_TEMPLATES = "settings:templates"
SETTINGS_PLAN = "settings:plan"
SETTINGS_ORGANIZATION = "settings:organization"
SETTINGS_EXPORT = "settings:export"
SETTINGS_DELETE_CLINIC = "settings:delete_clinic"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    [
        TODAY_VIEW,
        SCHEDULE_VIEW,
        WAITING_ROOM_VIEW,
        PATIENTS_VIEW,
        PATIENTS_CHART_SEARCH,
        BILLING_VIEW,
        OUTREACH_VIEW,
        DOCUMENTS_VIEW,
        INSIGHTS_VIEW,
        SCHEDULE_WRITE,
        PATIENTS_WRITE,
        PATIENTS_MERGE,
        BILLING_WRITE,
        BILLING_VOID,
        OUTREACH_MANAGE,
        DOCUMENTS_WRITE,
        REPORTS_VIEW,
        AUDIT_LOG_VIEW,
        SOAP_READ,
        SOAP_WRITE,
        PRESCRIPTIONS_WRITE,
        CHART_SEARCH,
        SETTINGS_ACCOUNT,
        SETTINGS_DOCTOR,
        SETTINGS_CLINIC,
        SETTINGS_TEAM,
        SETTINGS_SERVICES,
        SETTINGS_NOTIFICATIONS,
        SETTINGS_ASSISTANT,
        SETTINGS_TEMPLATES,
        SETTINGS_PLAN,
        SETTINGS_ORGANIZATION,
        SETTINGS_EXPORT,
        SETTINGS_DELETE_CLINIC,
    ]
)

# Role → base permissions (clinic flags may add more at runtime).
PERMISSIONS_BY_ROLE: dict[str, frozenset[str]] = {
    "owner": ALL_PERMISSIONS,
    "admin": ALL_PERMISSIONS - frozenset({SETTINGS_DELETE_CLINIC}),
    "doctor": frozenset(
        {
            TODAY_VIEW,
            SCHEDULE_VIEW,
            WAITING_ROOM_VIEW,
            PATIENTS_VIEW,
            PATIENTS_CHART_SEARCH,
            BILLING_VIEW,
            DOCUMENTS_VIEW,
            INSIGHTS_VIEW,
            SCHEDULE_WRITE,
            PATIENTS_WRITE,
            DOCUMENTS_WRITE,
            REPORTS_VIEW,
            AUDIT_LOG_VIEW,
            SOAP_READ,
            SOAP_WRITE,
            PRESCRIPTIONS_WRITE,
            CHART_SEARCH,
            SETTINGS_ACCOUNT,
            SETTINGS_DOCTOR,
        }
    ),
    "reception": frozenset(
        {
            TODAY_VIEW,
            SCHEDULE_VIEW,
            WAITING_ROOM_VIEW,
            PATIENTS_VIEW,
            BILLING_VIEW,
            OUTREACH_VIEW,
            SCHEDULE_WRITE,
            PATIENTS_WRITE,
            BILLING_WRITE,
            OUTREACH_MANAGE,
            SETTINGS_ACCOUNT,
        }
    ),
}

# Maps legacy require_clinic_role tuples to minimum permission sets.
ROLE_ALIASES: dict[str, frozenset[str]] = {
    "owner": frozenset({"owner"}),
    "admin": frozenset({"owner", "admin"}),
    "doctor": frozenset({"owner", "admin", "doctor"}),
    "reception": frozenset({"owner", "admin", "doctor", "reception"}),
}


def compute_permissions(membership: ClinicMembership, clinic: Clinic | None = None) -> list[str]:
    """Return sorted permission strings for the active membership."""
    role = membership.role
    base = set(PERMISSIONS_BY_ROLE.get(role, frozenset()))

    if clinic is not None and role == "reception" and clinic.reception_can_view_soap:
        base.add(PATIENTS_CHART_SEARCH)
        base.add(SOAP_READ)
        base.add(CHART_SEARCH)

    return sorted(base)


def role_has_any(role: str, allowed_roles: tuple[str, ...]) -> bool:
    return role in allowed_roles


def roles_for_clinic_staff() -> tuple[str, ...]:
    return ("owner", "admin", "doctor", "reception")


def roles_for_owner_admin() -> tuple[str, ...]:
    return ("owner", "admin")


def roles_for_owner_only() -> tuple[str, ...]:
    return ("owner",)
