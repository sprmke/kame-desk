import { Link } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, CircleDollarSign, RotateCcw, Shield } from "lucide-react";
import { api } from "@/lib/apiClient";
import type { OutstandingBalanceEntry, PatientRecall } from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { formatPhp } from "../lib/dashboardRange";
import {
  dashboardCardClass,
  dashboardFollowUpBodyClass,
} from "../lib/dashboardLayout";
import { DashboardCardHeader } from "./DashboardCardHeader";

function RowSkeleton() {
  return (
    <div className="flex flex-col gap-2 p-1">
      <Skeleton className="h-9 w-full" />
      <Skeleton className="h-9 w-full" />
      <Skeleton className="h-9 w-full" />
    </div>
  );
}

export function OutstandingCard({
  total,
  items,
  loading,
}: {
  total: string | null;
  items: OutstandingBalanceEntry[];
  loading: boolean;
}) {
  return (
    <Card className={dashboardCardClass}>
      <DashboardCardHeader
        title="Outstanding"
        to="/dashboard/billing/invoices"
      />
      <CardContent className={dashboardFollowUpBodyClass}>
        {loading ? (
          <RowSkeleton />
        ) : items.length === 0 ? (
          <EmptyState
            icon={CircleDollarSign}
            heading="No balances due"
            className="m-auto py-4"
          />
        ) : (
          <>
            <p className="px-2 pb-1 text-sm font-medium text-foreground">
              {formatPhp(total)}
            </p>
            <ul className="flex flex-col">
              {items.slice(0, 5).map((row) => (
                <li key={row.patient_id}>
                  <Link
                    to="/dashboard/patients/$patientId"
                    params={{ patientId: row.patient_id }}
                    className="flex min-h-11 items-center justify-between gap-2 rounded-lg px-2 py-2 text-sm native-press hover:bg-secondary"
                  >
                    <span className="min-w-0 truncate font-medium text-foreground">
                      {row.patient_name}
                    </span>
                    <span className="shrink-0 text-muted-foreground">
                      {formatPhp(row.outstanding_balance)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export function RecallsCard({
  items,
  loading,
}: {
  items: PatientRecall[];
  loading: boolean;
}) {
  return (
    <Card className={dashboardCardClass}>
      <DashboardCardHeader title="Recalls" to="/dashboard/recalls" />
      <CardContent className={dashboardFollowUpBodyClass}>
        {loading ? (
          <RowSkeleton />
        ) : items.length === 0 ? (
          <EmptyState
            icon={RotateCcw}
            heading="No recalls due"
            className="m-auto py-4"
          />
        ) : (
          <ul className="flex flex-col">
            {items.slice(0, 5).map((row) => (
              <li key={row.id}>
                <Link
                  to="/dashboard/appointments/new"
                  search={{ patientId: row.patient_id }}
                  className="flex min-h-11 items-center justify-between gap-2 rounded-lg px-2 py-2 text-sm native-press hover:bg-secondary"
                >
                  <span className="min-w-0 truncate font-medium text-foreground">
                    {row.patient_name ?? "Patient"}
                  </span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {row.due_date}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export function FailedRemindersCard({
  items,
  loading,
}: {
  items: Array<{
    id: string;
    patient_name?: string | null;
    channel: string;
  }>;
  loading: boolean;
}) {
  const qc = useQueryClient();
  const retry = useMutation({
    mutationFn: (id: string) => api.retryReminder(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["reminders"] });
    },
  });

  return (
    <Card className={dashboardCardClass}>
      <DashboardCardHeader title="Failed reminders" to="/dashboard/reminders" />
      <CardContent className={dashboardFollowUpBodyClass}>
        {loading ? (
          <RowSkeleton />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Bell}
            heading="No failed sends"
            className="m-auto py-4"
          />
        ) : (
          <ul className="flex flex-col">
            {items.slice(0, 5).map((row) => (
              <li
                key={row.id}
                className="flex min-h-11 items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-sm"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium text-foreground">
                    {row.patient_name ?? "Patient"}
                  </p>
                  <p className="text-xs text-muted-foreground">{row.channel}</p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="min-h-11"
                  loading={retry.isPending && retry.variables === row.id}
                  onClick={() => retry.mutate(row.id)}
                >
                  Retry
                </Button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export function OpenClaimsCard({
  items,
  loading,
}: {
  items: Array<{
    id: string;
    patient_name?: string | null;
    status: string;
    amount: string;
  }>;
  loading: boolean;
}) {
  return (
    <Card className={dashboardCardClass}>
      <DashboardCardHeader title="Claims" to="/dashboard/billing/claims" />
      <CardContent className={dashboardFollowUpBodyClass}>
        {loading ? (
          <RowSkeleton />
        ) : items.length === 0 ? (
          <EmptyState
            icon={Shield}
            heading="No open claims"
            className="m-auto py-4"
          />
        ) : (
          <ul className="flex flex-col">
            {items.slice(0, 5).map((row) => (
              <li key={row.id}>
                <Link
                  to="/dashboard/billing/claims/$claimId"
                  params={{ claimId: row.id }}
                  className="flex min-h-11 items-center justify-between gap-2 rounded-lg px-2 py-2 text-sm native-press hover:bg-secondary"
                >
                  <span className="min-w-0 truncate font-medium text-foreground">
                    {row.patient_name ?? "Patient"}
                  </span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {row.status} · {formatPhp(row.amount)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
