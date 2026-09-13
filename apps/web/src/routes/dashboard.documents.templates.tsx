import { createFileRoute } from "@tanstack/react-router";
import { RequirePermission } from "@/components/layout/RequirePermission";
import { DocumentTemplatesPage } from "@/features/documents/pages/DocumentTemplatesPage";

export const Route = createFileRoute("/dashboard/documents/templates")({
  component: DocumentTemplatesRoute,
});

function DocumentTemplatesRoute() {
  return (
    <RequirePermission permission="settings:templates">
      <DocumentTemplatesPage />
    </RequirePermission>
  );
}
