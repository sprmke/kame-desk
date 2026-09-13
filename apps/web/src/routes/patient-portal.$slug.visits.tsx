import { createFileRoute, redirect } from "@tanstack/react-router";
import {
  isPatientAuthenticated,
  shouldDeferPortalAuthRedirect,
} from "@/lib/patientPortalAuth";
import { PatientPortalVisitsPage } from "@/features/patient-portal/pages/PatientPortalVisitsPage";

export const Route = createFileRoute("/patient-portal/$slug/visits")({
  beforeLoad: ({ params }) => {
    if (shouldDeferPortalAuthRedirect()) return;
    if (!isPatientAuthenticated()) {
      throw redirect({
        to: "/patient-portal/$slug/login",
        params: { slug: params.slug },
      });
    }
  },
  component: PatientPortalVisitsRoute,
});

function PatientPortalVisitsRoute() {
  const { slug } = Route.useParams();
  return <PatientPortalVisitsPage slug={slug} />;
}
