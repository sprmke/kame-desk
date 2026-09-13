import { Outlet, createFileRoute } from "@tanstack/react-router";
import { RequirePermission } from "@/components/layout/RequirePermission";

export const Route = createFileRoute("/dashboard/billing")({
  component: BillingLayoutRoute,
});

// Hub tabs are applied per child route so claim detail, which is not a hub tab,
// does not inherit the Invoices / Claims switcher.
function BillingLayoutRoute() {
  return (
    <RequirePermission permission="billing:view">
      <Outlet />
    </RequirePermission>
  );
}
