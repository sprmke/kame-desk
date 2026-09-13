import { createFileRoute } from "@tanstack/react-router";
import { SectionHubLayout } from "@/components/layout/SectionHubLayout";
import { documentsHub } from "@/components/layout/nav-config";
import { RequirePermission } from "@/components/layout/RequirePermission";

export const Route = createFileRoute("/dashboard/documents")({
  component: DocumentsLayoutRoute,
});

function DocumentsLayoutRoute() {
  return (
    <RequirePermission permission="documents:view">
      <SectionHubLayout hub={documentsHub} />
    </RequirePermission>
  );
}
