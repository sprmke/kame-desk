import { createFileRoute } from "@tanstack/react-router";
import { DocumentGeneratePage } from "@/features/documents/pages/DocumentGeneratePage";

export const Route = createFileRoute("/dashboard/documents/generate")({
  component: DocumentGeneratePage,
});
