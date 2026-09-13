import { Outlet, createFileRoute } from "@tanstack/react-router";
import { RequirePermission } from "@/components/layout/RequirePermission";

export const Route = createFileRoute("/dashboard/appointments")({
  component: AppointmentsLayoutRoute,
});

// Hub tabs are applied per child route so booking and SOAP pages, which are not
// hub tabs, do not inherit the List / Calendar switcher.
function AppointmentsLayoutRoute() {
  return (
    <RequirePermission permission="schedule:view">
      <Outlet />
    </RequirePermission>
  );
}
