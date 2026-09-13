import { createFileRoute, redirect } from "@tanstack/react-router";
import {
  isPatientAuthenticated,
  shouldDeferPortalAuthRedirect,
} from "@/lib/patientPortalAuth";
import { PatientPortalChartPage } from "@/features/patient-portal/pages/PatientPortalChartPage";

export const Route = createFileRoute("/patient-portal/$slug/chart")({
  beforeLoad: ({ params }) => {
    if (shouldDeferPortalAuthRedirect()) return;
    if (!isPatientAuthenticated()) {
      throw redirect({
        to: "/patient-portal/$slug/login",
        params: { slug: params.slug },
      });
    }
  },
  component: PatientPortalChartRoute,
});

function PatientPortalChartRoute() {
  const { slug } = Route.useParams();
  return <PatientPortalChartPage slug={slug} />;
}
