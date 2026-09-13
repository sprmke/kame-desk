import { createFileRoute } from "@tanstack/react-router";
import { SectionHubLayout } from "@/components/layout/SectionHubLayout";
import { outreachHub } from "@/components/layout/nav-config";
import { RequirePermission } from "@/components/layout/RequirePermission";

export const Route = createFileRoute("/dashboard/outreach")({
  component: OutreachLayoutRoute,
});

function OutreachLayoutRoute() {
  return (
    <RequirePermission permission="outreach:view">
      <SectionHubLayout hub={outreachHub} />
    </RequirePermission>
  );
}
