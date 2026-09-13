import { createFileRoute } from "@tanstack/react-router";
import { RecallsPage } from "@/features/recalls/pages/RecallsPage";

export const Route = createFileRoute("/dashboard/outreach/recalls")({
  component: RecallsPage,
});
