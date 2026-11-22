import { createFileRoute } from "@tanstack/react-router";
import { SectionHubLayout } from "@/components/layout/SectionHubLayout";
import { documentsHub } from "@/components/layout/nav-config";

export const Route = createFileRoute("/dashboard/documents")({
  component: DocumentsLayoutRoute,
});

function DocumentsLayoutRoute() {
  return <SectionHubLayout hub={documentsHub} permission="documents:view" />;
}
