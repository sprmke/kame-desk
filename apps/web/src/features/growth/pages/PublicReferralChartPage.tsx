import { useQuery } from "@tanstack/react-query";
import { Activity, FileText } from "lucide-react";
import { api } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";

export function PublicReferralChartPage({ token }: { token: string }) {
  const chart = useQuery({
    queryKey: ["public-referral-chart", token],
    queryFn: () => api.getPublicReferralChart(token),
  });

  return (
    <div className="mx-auto min-h-screen max-w-2xl px-4 py-10">
      <h1 className="mb-1 text-lg font-semibold text-foreground">
        Shared chart summary
      </h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Read-only referral snapshot. This link expires and cannot be reused
        after that.
      </p>

      {chart.isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : chart.isError ? (
        <SectionCard>
          <ErrorState
            heading="This link is invalid or has expired"
            onRetry={() => chart.refetch()}
          />
        </SectionCard>
      ) : (
        <div className="flex flex-col gap-6">
          <section>
            <h2 className="mb-2 text-sm font-semibold text-muted-foreground">
              Diagnoses
            </h2>
            {chart.data && chart.data.diagnoses.length > 0 ? (
              <div className="flex flex-col gap-3">
                {chart.data.diagnoses.map((d, i) => (
                  <Card key={i}>
                    <CardContent className="py-4">
                      <p className="text-sm font-medium text-foreground">
                        {d.diagnosis_primary}
                      </p>
                      {d.diagnosis_secondary &&
                      d.diagnosis_secondary.length > 0 ? (
                        <p className="text-sm text-muted-foreground">
                          Also: {d.diagnosis_secondary.join(", ")}
                        </p>
                      ) : null}
                      <p className="mt-1 text-xs text-muted-foreground">
                        {new Date(d.visit_date).toLocaleDateString()} · Dr.{" "}
                        {d.doctor_name}
                        {d.follow_up_date
                          ? ` · Follow-up ${new Date(d.follow_up_date).toLocaleDateString()}`
                          : ""}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <SectionCard>
                <EmptyState
                  icon={FileText}
                  size="sm"
                  heading="No diagnoses recorded"
                />
              </SectionCard>
            )}
          </section>

          <section>
            <h2 className="mb-2 text-sm font-semibold text-muted-foreground">
              Vitals trend
            </h2>
            {chart.data && chart.data.vitals.length > 0 ? (
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Date</th>
                      <th className="px-3 py-2 font-medium">BP</th>
                      <th className="px-3 py-2 font-medium">HR</th>
                      <th className="px-3 py-2 font-medium">Weight</th>
                      <th className="px-3 py-2 font-medium">SpO2</th>
                    </tr>
                  </thead>
                  <tbody>
                    {chart.data.vitals.map((v, i) => (
                      <tr key={i} className="border-t border-border">
                        <td className="px-3 py-2 whitespace-nowrap text-foreground">
                          {new Date(v.recorded_at).toLocaleDateString()}
                        </td>
                        <td className="px-3 py-2 text-foreground">
                          {v.blood_pressure ?? "—"}
                        </td>
                        <td className="px-3 py-2 text-foreground">
                          {v.heart_rate ?? "—"}
                        </td>
                        <td className="px-3 py-2 text-foreground">
                          {v.weight_kg ? `${v.weight_kg} kg` : "—"}
                        </td>
                        <td className="px-3 py-2 text-foreground">
                          {v.spo2 ? `${v.spo2}%` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <SectionCard>
                <EmptyState
                  icon={Activity}
                  size="sm"
                  heading="No vitals recorded"
                />
              </SectionCard>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
