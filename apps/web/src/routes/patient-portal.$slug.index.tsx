import { createFileRoute, redirect } from "@tanstack/react-router";
import {
  isPatientAuthenticated,
  shouldDeferPortalAuthRedirect,
} from "@/lib/patientPortalAuth";

export const Route = createFileRoute("/patient-portal/$slug/")({
  beforeLoad: ({ params }) => {
    if (shouldDeferPortalAuthRedirect()) return;
    throw redirect({
      to: isPatientAuthenticated()
        ? "/patient-portal/$slug/visits"
        : "/patient-portal/$slug/login",
      params: { slug: params.slug },
    });
  },
});
