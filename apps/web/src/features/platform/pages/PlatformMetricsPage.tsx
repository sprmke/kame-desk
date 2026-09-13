import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState } from "@/components/ErrorState";

export function PlatformMetricsPage() {
  const { data, isError, refetch } = useQuery({
    queryKey: ["platform-metrics"],
    queryFn: () => api.getPlatformMetrics(),
  });

  return (
    <div className={pageContainerClass("narrow")}>
      <PageHeader title="Metrics" />
      {isError ? (
        <ErrorState onRetry={() => void refetch()} />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <MetricCard label="Appointments" value={data?.appointments_total} />
            <MetricCard label="AI requests" value={data?.ai_requests} />
            <MetricCard label="AI tokens" value={data?.ai_tokens} />
            <MetricCard label="SMS sent" value={data?.sms_sent} />
            <MetricCard label="SMS failed" value={data?.sms_failed} />
            <MetricCard label="Files" value={data?.files_total} />
          </div>
          <Card className="mt-4">
            <CardContent className="pt-5 text-sm">
              <p className="mb-2 font-medium text-foreground">Clinics</p>
              <ul className="flex flex-col gap-1 text-muted-foreground">
                {Object.entries(data?.clinics_by_status ?? {}).map(
                  ([status, count]) => (
                    <li key={status}>
                      {status}: {count}
                    </li>
                  ),
                )}
              </ul>
              {(data?.clinics_by_ai_requests ?? []).length > 0 ? (
                <ul className="mt-4 flex flex-col gap-1 text-muted-foreground">
                  {data?.clinics_by_ai_requests.map((row) => (
                    <li key={row.clinic_id}>
                      {row.name}: {row.ai_requests} AI
                    </li>
                  ))}
                </ul>
              ) : null}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value?: number }) {
  return (
    <Card>
      <CardContent className="pt-5">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold tabular-nums text-foreground">
          {value ?? 0}
        </p>
      </CardContent>
    </Card>
  );
}
