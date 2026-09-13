import { createFileRoute } from "@tanstack/react-router";
import { PublicReferralChartPage } from "@/features/growth/pages/PublicReferralChartPage";

export const Route = createFileRoute("/referral-chart/$token")({
  component: ReferralChartRoute,
});

function ReferralChartRoute() {
  const { token } = Route.useParams();
  return <PublicReferralChartPage token={token} />;
}
