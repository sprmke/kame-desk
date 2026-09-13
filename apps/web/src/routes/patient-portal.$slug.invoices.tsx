import { createFileRoute, redirect } from "@tanstack/react-router";
import {
  isPatientAuthenticated,
  shouldDeferPortalAuthRedirect,
} from "@/lib/patientPortalAuth";
import { PatientPortalInvoicesPage } from "@/features/patient-portal/pages/PatientPortalInvoicesPage";

export const Route = createFileRoute("/patient-portal/$slug/invoices")({
  beforeLoad: ({ params }) => {
    if (shouldDeferPortalAuthRedirect()) return;
    if (!isPatientAuthenticated()) {
      throw redirect({
        to: "/patient-portal/$slug/login",
        params: { slug: params.slug },
      });
    }
  },
  component: PatientPortalInvoicesRoute,
});

function PatientPortalInvoicesRoute() {
  const { slug } = Route.useParams();
  return <PatientPortalInvoicesPage slug={slug} />;
}
