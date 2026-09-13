import { createFileRoute } from "@tanstack/react-router";
import { ClaimDetailPage } from "@/features/billing/pages/ClaimDetailPage";

export const Route = createFileRoute("/dashboard/billing/claims/$claimId")({
  component: RouteComponent,
});

function RouteComponent() {
  const { claimId } = Route.useParams();
  return <ClaimDetailPage claimId={claimId} />;
}
