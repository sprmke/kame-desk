import { createFileRoute } from "@tanstack/react-router";
import { VerifyEmailPage } from "@/features/auth/pages/VerifyEmailPage";

type Search = { token?: string };

export const Route = createFileRoute("/verify-email")({
  validateSearch: (search: Record<string, unknown>): Search => ({
    token: typeof search.token === "string" ? search.token : undefined,
  }),
  component: VerifyEmailRoute,
});

function VerifyEmailRoute() {
  const { token } = Route.useSearch();
  return <VerifyEmailPage token={token ?? ""} />;
}
