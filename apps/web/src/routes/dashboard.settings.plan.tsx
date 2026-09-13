import { createFileRoute } from "@tanstack/react-router";
import { BillingPlanPage } from "@/features/settings/pages/BillingPlanPage";

export const Route = createFileRoute("/dashboard/settings/plan")({
  component: BillingPlanPage,
});
