import { useMemo, useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { CalendarDays } from "lucide-react";
import type { Appointment } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Calendar } from "@/components/ui/calendar";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { parseIsoDate, toIsoDate } from "@/lib/isoDate";
import { cn } from "@/lib/utils";
import {
  addDaysIso,
  formatManilaDayLabel,
  formatManilaTime,
} from "../lib/dashboardRange";
import {
  dashboardCardClass,
  dashboardWeekBodyClass,
} from "../lib/dashboardLayout";
import { bookedDates, groupUpcomingByDay } from "../lib/dashboardStats";
import { DashboardCardHeader } from "./DashboardCardHeader";

export function DashboardCalendarCard({
  items,
  today,
  loading,
  className,
}: {
  items: Appointment[];
  today: string;
  loading: boolean;
  className?: string;
}) {
  const navigate = useNavigate();
  const todayDate = parseIsoDate(today);
  const [month, setMonth] = useState(todayDate ?? new Date());
  const booked = useMemo(() => bookedDates(items), [items]);

  return (
    <Card className={cn(dashboardCardClass, className)}>
      <DashboardCardHeader
        title="Calendar"
        to="/dashboard/appointments/calendar"
      />
      <CardContent className={dashboardWeekBodyClass}>
        {loading ? (
          <div className="flex h-full flex-col gap-1">
            <div className="flex items-center justify-between px-1 pb-1">
              <Skeleton className="size-8 rounded-md" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="size-8 rounded-md" />
            </div>
            <div className="grid grid-cols-7 gap-1 px-1">
              {Array.from({ length: 7 }).map((_, index) => (
                <Skeleton key={index} className="mx-auto h-3 w-6" />
              ))}
            </div>
            <div className="grid flex-1 grid-cols-7 grid-rows-5 gap-1 px-1 pb-1">
              {Array.from({ length: 35 }).map((_, index) => (
                <Skeleton key={index} className="h-full min-h-6 w-full" />
              ))}
            </div>
          </div>
        ) : (
          <Calendar
            mode="single"
            month={month}
            onMonthChange={setMonth}
            selected={todayDate}
            onSelect={(day) => {
              if (!day) return;
              const iso = toIsoDate(day);
              void navigate({
                to: "/dashboard/appointments",
                search: { from: iso, to: iso },
              });
            }}
            modifiers={{ booked }}
            modifiersClassNames={{ booked: "has-appointments" }}
            className="fill"
          />
        )}
      </CardContent>
    </Card>
  );
}

export function UpcomingDaysStrip({
  items,
  today,
  loading,
  className,
  layout = "stack",
}: {
  items: Appointment[];
  today: string;
  loading: boolean;
  className?: string;
  layout?: "stack" | "strip";
}) {
  const groups = useMemo(
    () => groupUpcomingByDay(items, today, addDaysIso(today, 6)),
    [items, today],
  );
  const stacked = layout === "stack";

  return (
    <Card className={cn(dashboardCardClass, className)}>
      <DashboardCardHeader
        title="Upcoming"
        to="/dashboard/appointments/calendar"
      />
      <CardContent className={cn(dashboardWeekBodyClass, "overflow-y-auto")}>
        {loading ? (
          stacked ? (
            <div className="flex flex-col gap-2">
              {Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="min-w-0 px-2 pt-2 first:pt-0">
                  <Skeleton className="mb-1 h-3 w-20" />
                  <div className="flex min-h-11 items-center gap-3">
                    <Skeleton className="h-3.5 w-16 shrink-0" />
                    <Skeleton className="h-4 w-40 max-w-full" />
                  </div>
                  <div className="flex min-h-11 items-center gap-3">
                    <Skeleton className="h-3.5 w-16 shrink-0" />
                    <Skeleton className="h-4 w-32 max-w-full" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="min-w-0">
                  <Skeleton className="h-3 w-20" />
                  <div className="mt-1 flex min-h-11 items-center justify-between gap-2 py-1">
                    <Skeleton className="h-4 w-32 max-w-full" />
                    <Skeleton className="h-3 w-14 shrink-0" />
                  </div>
                  <div className="flex min-h-11 items-center justify-between gap-2 py-1">
                    <Skeleton className="h-4 w-28 max-w-full" />
                    <Skeleton className="h-3 w-14 shrink-0" />
                  </div>
                </div>
              ))}
            </div>
          )
        ) : groups.length === 0 ? (
          <EmptyState
            icon={CalendarDays}
            heading="Nothing in the next 7 days"
            size="sm"
            className="m-auto py-4"
          />
        ) : stacked ? (
          <ul className="flex flex-col">
            {groups.map((group) => (
              <li key={group.date} className="min-w-0 pt-2 first:pt-0">
                <p className="px-2 pb-0.5 text-xs font-medium text-muted-foreground">
                  {formatManilaDayLabel(group.date, today)}
                </p>
                <ul>
                  {group.items.map((appt) => (
                    <li key={appt.id}>
                      <Link
                        to="/dashboard/appointments/$appointmentId/soap"
                        params={{ appointmentId: appt.id }}
                        className="flex min-h-11 items-center gap-3 rounded-lg px-2 text-sm native-press hover:bg-secondary"
                      >
                        <span className="w-16 shrink-0 font-mono text-xs tabular-nums text-muted-foreground">
                          {formatManilaTime(appt.scheduled_start)}
                        </span>
                        <span className="min-w-0 truncate font-medium text-foreground">
                          {appt.patient_name ?? "Patient"}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        ) : (
          <ul className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
            {groups.map((group) => (
              <li key={group.date} className="min-w-0">
                <p className="text-xs font-medium text-muted-foreground">
                  {formatManilaDayLabel(group.date, today)}
                </p>
                <ul className="mt-1">
                  {group.items.slice(0, 4).map((appt) => (
                    <li key={appt.id}>
                      <Link
                        to="/dashboard/appointments/$appointmentId/soap"
                        params={{ appointmentId: appt.id }}
                        className="flex min-h-11 items-center justify-between gap-2 rounded-md py-1 text-sm native-press hover:bg-secondary"
                      >
                        <span className="min-w-0 truncate font-medium text-foreground">
                          {appt.patient_name ?? "Patient"}
                        </span>
                        <span className="shrink-0 font-mono text-xs tabular-nums text-muted-foreground">
                          {formatManilaTime(appt.scheduled_start)}
                        </span>
                      </Link>
                    </li>
                  ))}
                  {group.items.length > 4 ? (
                    <li className="px-0.5 text-xs text-muted-foreground">
                      +{group.items.length - 4}
                    </li>
                  ) : null}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
