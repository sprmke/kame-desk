import { createFileRoute } from "@tanstack/react-router";
import { ResetPasswordPage } from "@/features/auth/pages/ResetPasswordPage";

type Search = { token?: string };

export const Route = createFileRoute("/reset-password")({
  validateSearch: (search: Record<string, unknown>): Search => ({
    token: typeof search.token === "string" ? search.token : undefined,
  }),
  component: ResetPasswordRoute,
});

function ResetPasswordRoute() {
  const { token } = Route.useSearch();
  return <ResetPasswordPage token={token ?? ""} />;
}
