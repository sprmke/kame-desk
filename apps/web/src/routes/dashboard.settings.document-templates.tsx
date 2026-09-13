import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/layout/PageHeader";
import { DocumentTemplatesPage } from "@/features/documents/pages/DocumentTemplatesPage";

export const Route = createFileRoute("/dashboard/settings/document-templates")({
  component: DocumentTemplatesSettingsRoute,
});

// The page body is shared with the Documents section, which supplies its own
// fixed header. Under Settings the route provides the heading instead.
function DocumentTemplatesSettingsRoute() {
  return (
    <div>
      <PageHeader title="Document templates" />
      <DocumentTemplatesPage />
    </div>
  );
}
