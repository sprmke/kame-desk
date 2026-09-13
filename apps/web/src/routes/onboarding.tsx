import { createFileRoute, redirect } from "@tanstack/react-router";
import { OnboardingPage } from "@/features/onboarding/pages/OnboardingPage";
import { isAuthenticated, shouldDeferAuthRedirect } from "@/lib/auth";

export const Route = createFileRoute("/onboarding")({
  beforeLoad: () => {
    if (shouldDeferAuthRedirect()) return;
    if (!isAuthenticated()) throw redirect({ to: "/login" });
  },
  component: OnboardingPage,
});
