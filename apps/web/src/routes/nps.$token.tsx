import { createFileRoute } from "@tanstack/react-router";
import { PublicNpsPage } from "@/features/growth/pages/PublicNpsPage";

export const Route = createFileRoute("/nps/$token")({
  component: NpsRoute,
});

function NpsRoute() {
  const { token } = Route.useParams();
  return <PublicNpsPage token={token} />;
}
