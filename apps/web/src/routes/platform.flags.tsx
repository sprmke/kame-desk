import { createFileRoute } from "@tanstack/react-router";
import { PlatformFlagsPage } from "@/features/platform/pages/PlatformFlagsPage";

export const Route = createFileRoute("/platform/flags")({
  component: PlatformFlagsPage,
});
