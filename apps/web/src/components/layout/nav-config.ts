import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Bell,
  CalendarDays,
  FileText,
  LayoutDashboard,
  Receipt,
  Rows3,
  Users,
} from "lucide-react";
import type { Permission } from "@/lib/rbac";

export type NavLeaf = {
  label: string;
  to: string;
  icon: LucideIcon;
  permission: Permission;
};

export const mainNavItems: NavLeaf[] = [
  {
    label: "Today",
    to: "/dashboard",
    icon: LayoutDashboard,
    permission: "today:view",
  },
  {
    label: "Schedule",
    to: "/dashboard/appointments",
    icon: CalendarDays,
    permission: "schedule:view",
  },
  {
    label: "Waiting room",
    to: "/dashboard/waiting-room",
    icon: Rows3,
    permission: "waiting_room:view",
  },
  {
    label: "Patients",
    to: "/dashboard/patients",
    icon: Users,
    permission: "patients:view",
  },
  {
    label: "Billing",
    to: "/dashboard/billing",
    icon: Receipt,
    permission: "billing:view",
  },
  {
    label: "Outreach",
    to: "/dashboard/outreach",
    icon: Bell,
    permission: "outreach:view",
  },
  {
    label: "Documents",
    to: "/dashboard/documents",
    icon: FileText,
    permission: "documents:view",
  },
  {
    label: "Insights",
    to: "/dashboard/insights",
    icon: BarChart3,
    permission: "insights:view",
  },
];

export const bottomTabLeaves: NavLeaf[] = [
  {
    label: "Calendar",
    to: "/dashboard/appointments",
    icon: CalendarDays,
    permission: "schedule:view",
  },
  {
    label: "Waiting",
    to: "/dashboard/waiting-room",
    icon: Rows3,
    permission: "waiting_room:view",
  },
  {
    label: "Patients",
    to: "/dashboard/patients",
    icon: Users,
    permission: "patients:view",
  },
];

const bottomTabPaths = new Set(bottomTabLeaves.map((item) => item.to));

export function filterNavItems(
  items: NavLeaf[],
  can: (permission: Permission) => boolean,
): NavLeaf[] {
  return items.filter((item) => can(item.permission));
}

export function isBottomTabPath(pathname: string, to: string) {
  if (to === "/dashboard") return pathname === "/dashboard";
  return pathname === to || pathname.startsWith(`${to}/`);
}

export function bottomTabActiveKey(pathname: string): string | null {
  if (isBottomTabPath(pathname, "/dashboard/waiting-room")) return "waiting";
  if (isBottomTabPath(pathname, "/dashboard/patients")) return "patients";
  if (isBottomTabPath(pathname, "/dashboard/appointments")) return "calendar";
  return null;
}

export function moreNavItems(
  can: (permission: Permission) => boolean,
): NavLeaf[] {
  const items: NavLeaf[] = [];
  const today = mainNavItems.find((i) => i.to === "/dashboard");
  if (today && can(today.permission)) items.push(today);
  for (const item of mainNavItems) {
    if (item.to === "/dashboard") continue;
    if (bottomTabPaths.has(item.to)) continue;
    if (can(item.permission)) items.push(item);
  }
  return items;
}

export type SectionTab = {
  label: string;
  to: string;
  permission?: Permission;
};

export const scheduleTabs: SectionTab[] = [
  { label: "List", to: "/dashboard/appointments" },
  { label: "Calendar", to: "/dashboard/appointments/calendar" },
];

export const patientsTabs: SectionTab[] = [
  { label: "Directory", to: "/dashboard/patients" },
  {
    label: "Chart search",
    to: "/dashboard/patients/chart-search",
    permission: "patients:chart_search",
  },
];

export const billingTabs: SectionTab[] = [
  { label: "Invoices", to: "/dashboard/billing/invoices" },
  { label: "Claims", to: "/dashboard/billing/claims" },
  { label: "Eligibility", to: "/dashboard/billing/eligibility" },
  { label: "LOA", to: "/dashboard/billing/loa" },
];

export const outreachTabs: SectionTab[] = [
  { label: "Reminders", to: "/dashboard/outreach/reminders" },
  { label: "Recalls", to: "/dashboard/outreach/recalls" },
];

export const documentsTabs: SectionTab[] = [
  { label: "Generate", to: "/dashboard/documents/generate" },
  { label: "Templates", to: "/dashboard/documents/templates" },
];

export const insightsTabs: SectionTab[] = [
  { label: "Reports", to: "/dashboard/insights/reports" },
  { label: "Activity log", to: "/dashboard/insights/audit-log" },
];

export type SectionHub = {
  /** Fixed page title. Matches the sidebar nav label. */
  title: string;
  tabs: SectionTab[];
};

export const scheduleHub: SectionHub = {
  title: "Schedule",
  tabs: scheduleTabs,
};

export const patientsHub: SectionHub = {
  title: "Patients",
  tabs: patientsTabs,
};

export const billingHub: SectionHub = {
  title: "Billing",
  tabs: billingTabs,
};

export const outreachHub: SectionHub = {
  title: "Outreach",
  tabs: outreachTabs,
};

export const documentsHub: SectionHub = {
  title: "Documents",
  tabs: documentsTabs,
};

export const insightsHub: SectionHub = {
  title: "Insights",
  tabs: insightsTabs,
};

const hubTabGroups: SectionTab[][] = [
  scheduleTabs,
  patientsTabs,
  billingTabs,
  outreachTabs,
  documentsTabs,
  insightsTabs,
];

/**
 * Sibling tabs of one section share a transition key so switching tabs swaps
 * only the content. The fixed section header must not re-animate.
 */
export function pageTransitionKey(pathname: string): string {
  const normalized =
    pathname.length > 1 && pathname.endsWith("/")
      ? pathname.slice(0, -1)
      : pathname;
  const group = hubTabGroups.find((tabs) =>
    tabs.some((tab) => tab.to === normalized),
  );
  return group?.[0].to ?? pathname;
}
