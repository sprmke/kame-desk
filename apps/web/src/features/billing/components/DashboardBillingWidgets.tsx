import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function RevenueWidget() {
  const clinicId = getClinicId();
  const { data } = useQuery({
    queryKey: ["revenue-report-totals", clinicId],
    queryFn: () => api.getRevenueReport({}),
    enabled: Boolean(clinicId),
  });

  const totals = data?.totals;
  if (!totals) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-3 gap-3 text-sm">
          <div>
            <dt className="text-muted-foreground">Today</dt>
            <dd className="text-base font-semibold text-foreground">
              PHP {totals.today}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Week</dt>
            <dd className="text-base font-semibold text-foreground">
              PHP {totals.week}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Month</dt>
            <dd className="text-base font-semibold text-foreground">
              PHP {totals.month}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

export function OutstandingWidget() {
  const clinicId = getClinicId();
  const { data } = useQuery({
    queryKey: ["outstanding-balances", clinicId],
    queryFn: () => api.getOutstandingBalances(clinicId!),
    enabled: Boolean(clinicId),
  });

  if (!data) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Outstanding</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-2 text-sm text-muted-foreground">
          Total:{" "}
          <span className="font-medium text-foreground">
            PHP {data.total_outstanding}
          </span>
        </p>
        {(data.items ?? []).length === 0 ? (
          <p className="text-sm text-muted-foreground">None</p>
        ) : (
          <ul className="flex flex-col divide-y divide-border text-sm">
            {data.items.slice(0, 5).map((row) => (
              <li
                key={row.patient_id}
                className="flex justify-between py-2 first:pt-0 last:pb-0"
              >
                <Link
                  to="/dashboard/patients/$patientId"
                  params={{ patientId: row.patient_id }}
                  className="font-medium text-primary hover:underline"
                >
                  {row.patient_name}
                </Link>
                <span className="text-muted-foreground">
                  PHP {row.outstanding_balance}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
