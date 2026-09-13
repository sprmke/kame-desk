import { Link } from "@tanstack/react-router";
import { CalendarDays } from "lucide-react";
import type { Appointment } from "@/lib/apiClient";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { formatManilaTime } from "../lib/dashboardRange";
import {
  dashboardCardClass,
  dashboardListBodyClass,
} from "../lib/dashboardLayout";
import {
  nextAppointmentId,
  visitOrAppointmentStatus,
} from "../lib/dashboardStats";
import { DashboardCardHeader } from "./DashboardCardHeader";

const statusVariant: Record<
  string,
  "success" | "warning" | "info" | "default" | "brand" | "error"
> = {
  Confirmed: "success",
  Scheduled: "info",
  Arrived: "warning",
  "In Consultation": "brand",
  Completed: "success",
  "No Show": "warning",
  Cancelled: "error",
  Rescheduled: "default",
};

export function TodayScheduleCard({
  items,
  loading,
}: {
  items: Appointment[];
  loading: boolean;
}) {
  const nextId = nextAppointmentId(items);

  return (
    <Card className={cn(dashboardCardClass, "lg:col-span-2")}>
      <DashboardCardHeader title="Today" to="/dashboard/appointments" />
      <CardContent
        className={cn(dashboardListBodyClass, "flex flex-col gap-0.5")}
      >
        {loading ? (
          <div className="flex flex-col gap-2 p-2">
            <Skeleton className="h-11 w-full" />
            <Skeleton className="h-11 w-full" />
            <Skeleton className="h-11 w-full" />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={CalendarDays}
            heading="No appointments today"
            size="sm"
            className="m-auto py-4"
          />
        ) : (
          items.map((appt) => {
            const status = visitOrAppointmentStatus(appt);
            return (
              <Link
                key={appt.id}
                to="/dashboard/appointments/$appointmentId/soap"
                params={{ appointmentId: appt.id }}
                className={cn(
                  "flex min-h-11 items-center gap-3 rounded-lg px-2 py-2 text-sm native-press hover:bg-secondary",
                  appt.id === nextId && "bg-brand-50/80 dark:bg-accent/40",
                )}
              >
                <span className="w-14 shrink-0 font-mono text-xs tabular-nums text-muted-foreground">
                  {formatManilaTime(appt.scheduled_start)}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-foreground">
                    {appt.patient_name ?? "Patient"}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {appt.doctor_name ?? "Doctor"}
                    {appt.reason_for_visit ? ` · ${appt.reason_for_visit}` : ""}
                  </p>
                </div>
                <Badge variant={statusVariant[status] ?? "default"} dot>
                  {status}
                </Badge>
              </Link>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
