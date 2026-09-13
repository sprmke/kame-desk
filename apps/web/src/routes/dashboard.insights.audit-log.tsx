import { createFileRoute } from "@tanstack/react-router";
import { RequirePermission } from "@/components/layout/RequirePermission";
import { AuditLogPage } from "@/features/audit-log/pages/AuditLogPage";

export const Route = createFileRoute("/dashboard/insights/audit-log")({
  component: InsightsAuditLogRoute,
});

function InsightsAuditLogRoute() {
  return (
    <RequirePermission permission="audit_log:view">
      <AuditLogPage />
    </RequirePermission>
  );
}
