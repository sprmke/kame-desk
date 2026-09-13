import { createFileRoute } from "@tanstack/react-router";
import { MembershipPlansSettingsPage } from "@/features/settings/membership/pages/MembershipPlansSettingsPage";

export const Route = createFileRoute("/dashboard/settings/membership-plans")({
  component: MembershipPlansSettingsPage,
});
