import { createFileRoute } from "@tanstack/react-router";
import { SectionHubShell } from "@/components/layout/SectionHubShell";
import { billingHub } from "@/components/layout/nav-config";
import { InvoiceListPage } from "@/features/billing/pages/InvoiceListPage";

export const Route = createFileRoute("/dashboard/billing/invoices")({
  component: InvoiceListRoute,
});

function InvoiceListRoute() {
  return (
    <SectionHubShell hub={billingHub}>
      <InvoiceListPage />
    </SectionHubShell>
  );
}
