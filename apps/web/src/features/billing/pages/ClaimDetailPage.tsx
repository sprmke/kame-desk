import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft } from "lucide-react";
import { api } from "@/lib/apiClient";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { ClaimsPageSkeleton } from "@/components/skeletons/PageSkeletons";

export function ClaimDetailPage({ claimId }: { claimId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["claims", claimId],
    queryFn: async () => {
      const res = await api.listClaims({ page_size: 100 });
      return res.items.find((c) => c.id === claimId) ?? null;
    },
  });

  if (isLoading) return <ClaimsPageSkeleton />;

  if (!data) {
    return <p className="text-sm text-muted-foreground">Claim not found.</p>;
  }

  return (
    <div className={pageContainerClass("narrow")}>
      <Link
        to="/dashboard/billing/claims"
        className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="size-4" />
        Claims
      </Link>
      <PageHeader
        title="Claim"
        description={`${data.patient_name ?? "Patient"} · ${data.provider}`}
      />
      <Card>
        <CardContent className="grid gap-2 pt-5 text-sm">
          <p>
            <span className="text-muted-foreground">Status:</span> {data.status}
          </p>
          <p>
            <span className="text-muted-foreground">Payer:</span>{" "}
            {data.payer_type}
          </p>
          <p>
            <span className="text-muted-foreground">Amount:</span> PHP{" "}
            {data.amount}
          </p>
          {data.notes ? (
            <p>
              <span className="text-muted-foreground">Notes:</span> {data.notes}
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
