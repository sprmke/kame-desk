import { createFileRoute } from "@tanstack/react-router";
import { AssistantSettingsPage } from "@/features/settings/assistant/pages/AssistantSettingsPage";

export const Route = createFileRoute("/dashboard/settings/assistant")({
  component: AssistantSettingsPage,
});
