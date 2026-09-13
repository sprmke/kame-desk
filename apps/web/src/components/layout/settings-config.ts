import type { LucideIcon } from "lucide-react";
import {
  Bell,
  Building2,
  CircleUser,
  FileText,
  MessageSquare,
  UserCog,
  UserRound,
  Wallet,
} from "lucide-react";
import type { Permission } from "@/lib/rbac";

export type SettingsItem = {
  label: string;
  to: string;
  icon: LucideIcon;
  permission: Permission;
};

export type SettingsGroup = {
  label: string;
  items: SettingsItem[];
};

export const settingsGroups: SettingsGroup[] = [
  {
    label: "Personal",
    items: [
      {
        label: "Account",
        to: "/dashboard/settings/account",
        icon: CircleUser,
        permission: "settings:account",
      },
      {
        label: "Doctor profile",
        to: "/dashboard/settings/doctor",
        icon: UserRound,
        permission: "settings:doctor",
      },
    ],
  },
  {
    label: "Clinic",
    items: [
      {
        label: "Details",
        to: "/dashboard/settings/clinic/details",
        icon: Building2,
        permission: "settings:clinic",
      },
      {
        label: "Hours and holidays",
        to: "/dashboard/settings/clinic/hours",
        icon: Building2,
        permission: "settings:clinic",
      },
      {
        label: "Rooms",
        to: "/dashboard/settings/clinic/rooms",
        icon: Building2,
        permission: "settings:clinic",
      },
      {
        label: "Branding",
        to: "/dashboard/settings/clinic/branding",
        icon: Building2,
        permission: "settings:clinic",
      },
      {
        label: "Compliance",
        to: "/dashboard/settings/clinic/compliance",
        icon: Building2,
        permission: "settings:clinic",
      },
      {
        label: "Services and fees",
        to: "/dashboard/settings/services",
        icon: Wallet,
        permission: "settings:services",
      },
      {
        label: "Payers",
        to: "/dashboard/settings/payers",
        icon: Wallet,
        permission: "billing:view",
      },
      {
        label: "Membership plans",
        to: "/dashboard/settings/membership-plans",
        icon: Wallet,
        permission: "settings:services",
      },
      {
        label: "Document templates",
        to: "/dashboard/settings/document-templates",
        icon: FileText,
        permission: "settings:templates",
      },
    ],
  },
  {
    label: "Team",
    items: [
      {
        label: "Members",
        to: "/dashboard/settings/team",
        icon: UserCog,
        permission: "settings:team",
      },
    ],
  },
  {
    label: "Automation",
    items: [
      {
        label: "Notifications",
        to: "/dashboard/settings/notifications",
        icon: Bell,
        permission: "settings:notifications",
      },
      {
        label: "Assistant",
        to: "/dashboard/settings/assistant",
        icon: MessageSquare,
        permission: "settings:assistant",
      },
    ],
  },
  {
    label: "Plan",
    items: [
      {
        label: "Organization",
        to: "/dashboard/settings/organization",
        icon: Building2,
        permission: "settings:organization",
      },
      {
        label: "Billing plan",
        to: "/dashboard/settings/plan",
        icon: Wallet,
        permission: "settings:plan",
      },
    ],
  },
];

export function filterSettingsGroups(
  can: (permission: Permission) => boolean,
): SettingsGroup[] {
  return settingsGroups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => can(item.permission)),
    }))
    .filter((group) => group.items.length > 0);
}
