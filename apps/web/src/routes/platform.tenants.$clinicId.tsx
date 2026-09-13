import { createFileRoute } from "@tanstack/react-router";
import { PlatformTenantDetailPage } from "@/features/platform/pages/PlatformTenantDetailPage";

export const Route = createFileRoute("/platform/tenants/$clinicId")({
  component: TenantDetailRoute,
});

function TenantDetailRoute() {
  const { clinicId } = Route.useParams();
  return <PlatformTenantDetailPage clinicId={clinicId} />;
}
