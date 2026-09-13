import { createFileRoute } from "@tanstack/react-router";
import { PatientNewPage } from "@/features/patients/pages/PatientNewPage";

export const Route = createFileRoute("/dashboard/patients/new")({
  component: PatientNewPage,
});
