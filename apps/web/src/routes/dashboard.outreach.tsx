import { createFileRoute } from "@tanstack/react-router";
import { SectionHubLayout } from "@/components/layout/SectionHubLayout";
import { outreachHub } from "@/components/layout/nav-config";

export const Route = createFileRoute("/dashboard/outreach")({
  component: OutreachLayoutRoute,
});

function OutreachLayoutRoute() {
  return <SectionHubLayout hub={outreachHub} permission="outreach:view" />;
}
