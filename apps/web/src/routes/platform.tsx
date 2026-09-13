import { createFileRoute, redirect } from "@tanstack/react-router";
import { isAuthenticated, shouldDeferAuthRedirect } from "@/lib/auth";
import { PlatformShell } from "@/features/platform/components/PlatformShell";

export const Route = createFileRoute("/platform")({
  beforeLoad: () => {
    if (shouldDeferAuthRedirect()) return;
    if (!isAuthenticated()) {
      throw redirect({ to: "/login" });
    }
  },
  component: PlatformShell,
});
