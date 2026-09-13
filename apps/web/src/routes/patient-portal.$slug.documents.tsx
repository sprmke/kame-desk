import { createFileRoute, redirect } from "@tanstack/react-router";
import {
  isPatientAuthenticated,
  shouldDeferPortalAuthRedirect,
} from "@/lib/patientPortalAuth";
import { PatientPortalDocumentsPage } from "@/features/patient-portal/pages/PatientPortalDocumentsPage";

export const Route = createFileRoute("/patient-portal/$slug/documents")({
  beforeLoad: ({ params }) => {
    if (shouldDeferPortalAuthRedirect()) return;
    if (!isPatientAuthenticated()) {
      throw redirect({
        to: "/patient-portal/$slug/login",
        params: { slug: params.slug },
      });
    }
  },
  component: PatientPortalDocumentsRoute,
});

function PatientPortalDocumentsRoute() {
  const { slug } = Route.useParams();
  return <PatientPortalDocumentsPage slug={slug} />;
}
