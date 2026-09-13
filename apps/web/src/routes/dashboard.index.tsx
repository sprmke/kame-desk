import { createFileRoute } from "@tanstack/react-router";
import { DashboardOverviewPage } from "@/features/dashboard/pages/DashboardOverviewPage";

export const Route = createFileRoute("/dashboard/")({
  component: DashboardOverviewPage,
});
