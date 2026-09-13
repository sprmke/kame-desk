/** Permission strings — must match apps/api/app/core/permissions.py */

export type Permission =
  | "today:view"
  | "schedule:view"
  | "waiting_room:view"
  | "patients:view"
  | "patients:chart_search"
  | "billing:view"
  | "outreach:view"
  | "documents:view"
  | "insights:view"
  | "schedule:write"
  | "patients:write"
  | "patients:merge"
  | "billing:write"
  | "billing:void"
  | "outreach:manage"
  | "documents:write"
  | "reports:view"
  | "audit_log:view"
  | "soap:read"
  | "soap:write"
  | "prescriptions:write"
  | "chart_search:use"
  | "settings:account"
  | "settings:doctor"
  | "settings:clinic"
  | "settings:team"
  | "settings:services"
  | "settings:notifications"
  | "settings:assistant"
  | "settings:templates"
  | "settings:plan"
  | "settings:organization"
  | "settings:export"
  | "settings:delete_clinic";

export type ClinicRole = "owner" | "admin" | "doctor" | "reception";

export function can(
  permissions: readonly string[] | undefined,
  permission: Permission,
): boolean {
  return permissions?.includes(permission) ?? false;
}

export function canAny(
  permissions: readonly string[] | undefined,
  required: Permission[],
): boolean {
  return required.some((p) => can(permissions, p));
}

export function defaultLandingPath(role: ClinicRole | undefined): string {
  if (role === "reception") return "/dashboard/waiting-room";
  return "/dashboard";
}

export const ROLE_LABELS: Record<ClinicRole, string> = {
  owner: "Owner",
  admin: "Admin",
  doctor: "Doctor",
  reception: "Reception",
};
