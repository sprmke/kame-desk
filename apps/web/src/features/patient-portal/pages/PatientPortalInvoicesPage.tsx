import { useQuery } from "@tanstack/react-query";
import { Receipt } from "lucide-react";
import { PatientPortalAppShell } from "@/features/patient-portal/components/PatientPortalAppShell";
import { patientPortalApi } from "@/features/patient-portal/lib/patientPortalClient";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";

const STATUS_VARIANT: Record<
  string,
  "success" | "warning" | "outline" | "error"
> = {
  paid: "success",
  partially_paid: "warning",
  issued: "outline",
  void: "error",
};

export function PatientPortalInvoicesPage({ slug }: { slug: string }) {
  const me = useQuery({
    queryKey: ["portal-me"],
    queryFn: patientPortalApi.getMe,
  });
  const invoices = useQuery({
    queryKey: ["portal-invoices"],
    queryFn: patientPortalApi.getInvoices,
  });

  return (
    <PatientPortalAppShell
      slug={slug}
      clinicName={me.data?.clinic_name}
      patientName={me.data?.full_name}
    >
      <h1 className="mb-4 text-lg font-semibold text-foreground">Billing</h1>

      {invoices.isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : invoices.isError ? (
        <SectionCard>
          <ErrorState
            heading="Could not load your invoices"
            onRetry={() => invoices.refetch()}
          />
        </SectionCard>
      ) : invoices.data ? (
        <div className="flex flex-col gap-4">
          {Number(invoices.data.total_balance) > 0 ? (
            <Card className="border-warning-500/30 bg-warning-50 dark:bg-warning/10">
              <CardContent className="py-3">
                <p className="text-sm font-medium text-foreground">
                  Outstanding balance: ₱
                  {Number(invoices.data.total_balance).toLocaleString()}
                </p>
              </CardContent>
            </Card>
          ) : null}

          {invoices.data.items.length > 0 ? (
            <div className="flex flex-col gap-3">
              {invoices.data.items.map((inv) => (
                <Card key={inv.id}>
                  <CardContent className="flex items-center justify-between gap-3 py-4">
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        {inv.invoice_number ?? "Invoice"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Total ₱{Number(inv.total).toLocaleString()}
                        {Number(inv.balance) > 0
                          ? ` · Balance ₱${Number(inv.balance).toLocaleString()}`
                          : ""}
                      </p>
                    </div>
                    <Badge variant={STATUS_VARIANT[inv.status] ?? "outline"}>
                      {inv.status.replace("_", " ")}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <SectionCard>
              <EmptyState icon={Receipt} heading="No invoices yet" />
            </SectionCard>
          )}
        </div>
      ) : null}
    </PatientPortalAppShell>
  );
}
