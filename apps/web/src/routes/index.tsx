import { createFileRoute, redirect } from "@tanstack/react-router";
import { isAuthenticated, shouldDeferAuthRedirect } from "@/lib/auth";

export const Route = createFileRoute("/")({
  beforeLoad: () => {
    if (shouldDeferAuthRedirect()) return;
    throw redirect({ to: isAuthenticated() ? "/dashboard" : "/login" });
  },
});
