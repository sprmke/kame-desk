import { createFileRoute } from "@tanstack/react-router";
import { PlatformTenantsPage } from "@/features/platform/pages/PlatformTenantsPage";

export const Route = createFileRoute("/platform/")({
  component: PlatformTenantsPage,
});
