import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { isAuthenticated, shouldDeferAuthRedirect } from "@/lib/auth";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { CompactNotFoundPage } from "@/components/layout/NotFoundPage";

export const Route = createFileRoute("/dashboard")({
  beforeLoad: () => {
    if (shouldDeferAuthRedirect()) return;
    if (!isAuthenticated()) {
      throw redirect({ to: "/login" });
    }
  },
  notFoundComponent: CompactNotFoundPage,
  component: DashboardLayout,
});

function DashboardLayout() {
  return (
    <DashboardShell>
      <Outlet />
    </DashboardShell>
  );
}
