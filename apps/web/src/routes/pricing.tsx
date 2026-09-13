import { createFileRoute } from "@tanstack/react-router";
import { PricingPage } from "@/features/marketing/pages/PricingPage";

export const Route = createFileRoute("/pricing")({
  component: PricingPage,
});
