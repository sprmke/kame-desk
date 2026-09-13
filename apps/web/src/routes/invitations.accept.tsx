import { createFileRoute } from "@tanstack/react-router";
import { InvitationAcceptPage } from "@/features/onboarding/pages/InvitationAcceptPage";

type Search = { token?: string };

export const Route = createFileRoute("/invitations/accept")({
  validateSearch: (search: Record<string, unknown>): Search => ({
    token: typeof search.token === "string" ? search.token : undefined,
  }),
  component: InvitationAcceptRoute,
});

function InvitationAcceptRoute() {
  const { token } = Route.useSearch();
  return <InvitationAcceptPage token={token ?? ""} />;
}
