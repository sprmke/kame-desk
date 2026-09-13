import { createFileRoute } from "@tanstack/react-router";
import { PatientPortalVerifyPage } from "@/features/patient-portal/pages/PatientPortalVerifyPage";

type Search = { token?: string };

export const Route = createFileRoute("/patient-portal/$slug/verify")({
  validateSearch: (search: Record<string, unknown>): Search => ({
    token: typeof search.token === "string" ? search.token : undefined,
  }),
  component: PatientPortalVerifyRoute,
});

function PatientPortalVerifyRoute() {
  const { slug } = Route.useParams();
  const { token } = Route.useSearch();
  return <PatientPortalVerifyPage slug={slug} token={token} />;
}
