import { createFileRoute } from "@tanstack/react-router";
import { PatientPortalLoginPage } from "@/features/patient-portal/pages/PatientPortalLoginPage";

export const Route = createFileRoute("/patient-portal/$slug/login")({
  component: PatientPortalLoginRoute,
});

function PatientPortalLoginRoute() {
  const { slug } = Route.useParams();
  return <PatientPortalLoginPage slug={slug} />;
}
