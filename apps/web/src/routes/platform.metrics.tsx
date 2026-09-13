import { createFileRoute } from "@tanstack/react-router";
import { PlatformMetricsPage } from "@/features/platform/pages/PlatformMetricsPage";

export const Route = createFileRoute("/platform/metrics")({
  component: PlatformMetricsPage,
});
