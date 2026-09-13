import { Link } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { UserPlus, Users } from "lucide-react";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { useSession } from "@/hooks/useSession";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AppointmentsTrendChart } from "@/components/charts/AppointmentsTrendChart";
import { DashboardOverviewSkeleton } from "@/components/skeletons/PageSkeletons";
import { ErrorState } from "@/components/ErrorState";
import { WalkInDialog } from "@/features/waiting-room/components/WalkInDialog";
import { useWaitingRoom } from "@/features/waiting-room/hooks/useWaitingRoom";
import { cn } from "@/lib/utils";
import { addDaysIso, dashboardAppointmentWindow } from "../lib/dashboardRange";
import {
  dashboardCardClass,
  dashboardChartBodyClass,
} from "../lib/dashboardLayout";
import { DashboardCardHeader } from "../components/DashboardCardHeader";
import {
  activeAppointmentCount,
  appointmentsOnDate,
  completedVisitCount,
  notOnFloor,
  OPEN_CLAIM_STATUSES,
  scheduledWaitingCount,
  waitingNowCount,
} from "../lib/dashboardStats";
import { DashboardKpiRow } from "../components/DashboardKpiRow";
import { TodayScheduleCard } from "../components/TodayScheduleCard";
import { WaitingQueueCard } from "../components/WaitingQueueCard";
import {
  DashboardCalendarCard,
  UpcomingDaysStrip,
} from "../components/UpcomingCard";
import {
  FailedRemindersCard,
  OpenClaimsCard,
  OutstandingCard,
  RecallsCard,
} from "../components/AttentionCards";

export function DashboardOverviewPage() {
  const clinicId = getClinicId();
  const range = useMemo(() => dashboardAppointmentWindow(), []);
  const [walkInOpen, setWalkInOpen] = useState(false);
  const queryClient = useQueryClient();

  function closeWalkIn() {
    setWalkInOpen(false);
    void queryClient.invalidateQueries({ queryKey: ["waiting-room"] });
    void queryClient.invalidateQueries({ queryKey: ["appointments"] });
  }

  const { role, can } = useSession();
  const canRecalls = can("outreach:manage");
  const showRecalls = role !== "doctor";
  const showTrend = can("reports:view");
  const trend = useMemo(
    () => ({
      from_date: addDaysIso(range.today, -13),
      to_date: range.today,
    }),
    [range.today],
  );

  const {
    data: appointments,
    isLoading: loadingAppointments,
    isError: appointmentsError,
    refetch: refetchAppointments,
  } = useQuery({
    queryKey: ["appointments", "dashboard", range.start_from, range.start_to],
    queryFn: () =>
      api.listAppointments({
        start_from: range.start_from,
        start_to: range.start_to,
      }),
  });

  const { data: waiting, isLoading: loadingWaiting } = useWaitingRoom();

  const { data: revenue, isLoading: loadingRevenue } = useQuery({
    queryKey: ["dashboard-revenue", clinicId],
    queryFn: () => api.getRevenueSummary(clinicId!),
    enabled: Boolean(clinicId),
  });

  const { data: outstanding, isLoading: loadingOutstanding } = useQuery({
    queryKey: ["outstanding-balances", clinicId],
    queryFn: () => api.getOutstandingBalances(clinicId!),
    enabled: Boolean(clinicId),
  });

  const { data: recalls, isLoading: loadingRecalls } = useQuery({
    queryKey: ["recalls", clinicId],
    queryFn: () => api.listRecalls(clinicId!),
    enabled: Boolean(clinicId) && canRecalls,
  });

  const { data: failedReminders, isLoading: loadingReminders } = useQuery({
    queryKey: ["reminders", "failed"],
    queryFn: () => api.listReminders("failed"),
  });

  const { data: claims, isLoading: loadingClaims } = useQuery({
    queryKey: ["claims", "dashboard-open"],
    queryFn: () => api.listClaims(),
  });

  const { data: trendReport, isLoading: loadingTrend } = useQuery({
    queryKey: ["reports", "appointments", "dashboard-trend", trend],
    queryFn: () =>
      api.getAppointmentsReport({
        from_date: trend.from_date,
        to_date: trend.to_date,
        group_by: "day",
      }),
    enabled: showTrend,
  });

  const header = (
    <PageHeader
      title="Dashboard"
      actions={
        <>
          <Link
            to="/dashboard/patients/new"
            className={cn(
              buttonVariants({ variant: "outline", size: "sm" }),
              "min-h-11",
            )}
          >
            <Users className="size-4" />
            New patient
          </Link>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="min-h-11"
            onClick={() => setWalkInOpen(true)}
          >
            <UserPlus className="size-4" />
            Walk-in
          </Button>
          <Link
            to="/dashboard/appointments/new"
            search={{ patientId: undefined }}
            className={cn(buttonVariants({ size: "sm" }), "min-h-11")}
          >
            New appointment
          </Link>
        </>
      }
    />
  );

  if (loadingAppointments && !appointments) {
    return (
      <PageContainer>
        {header}
        <DashboardOverviewSkeleton />
        <WalkInDialog
          open={walkInOpen}
          onOpenChange={setWalkInOpen}
          onDone={closeWalkIn}
        />
      </PageContainer>
    );
  }

  if (appointmentsError && !appointments) {
    return (
      <PageContainer>
        {header}
        <ErrorState onRetry={() => void refetchAppointments()} />
        <WalkInDialog
          open={walkInOpen}
          onOpenChange={setWalkInOpen}
          onDone={closeWalkIn}
        />
      </PageContainer>
    );
  }

  const allAppointments = appointments?.items ?? [];
  const todaysAppointments = appointmentsOnDate(allAppointments, range.today);
  const scheduleItems = todaysAppointments.filter(notOnFloor);
  const waitingItems = waiting?.items ?? [];
  const openClaims = (claims?.items ?? []).filter((row) =>
    OPEN_CLAIM_STATUSES.has(row.status),
  );
  const trendPoints = (trendReport?.series ?? []).map((row) => ({
    date: String(row.period ?? ""),
    booked: Number(row.booked ?? 0),
    completed: Number(row.completed ?? 0),
  }));

  return (
    <PageContainer>
      {header}

      <DashboardKpiRow
        todayCount={activeAppointmentCount(todaysAppointments)}
        waitingCount={waitingNowCount(waitingItems)}
        scheduledWaiting={scheduledWaitingCount(waitingItems)}
        completedCount={completedVisitCount(waitingItems)}
        monthRevenue={revenue?.month ?? null}
        todayRevenue={revenue?.today ?? null}
        weekRevenue={revenue?.week ?? null}
        loadingToday={loadingAppointments}
        loadingWaiting={loadingWaiting}
        loadingRevenue={loadingRevenue}
      />

      <div className="mt-4 grid grid-cols-1 items-stretch gap-4 lg:grid-cols-3">
        <TodayScheduleCard
          items={scheduleItems}
          loading={loadingAppointments}
        />
        <WaitingQueueCard items={waitingItems} loading={loadingWaiting} />
      </div>

      {showTrend ? (
        <div className="mt-4 grid grid-cols-1 items-stretch gap-4 lg:grid-cols-3">
          <Card className={cn(dashboardCardClass, "lg:col-span-2")}>
            <DashboardCardHeader
              title="Appointments, last 14 days"
              to="/dashboard/reports"
            />
            <CardContent className={dashboardChartBodyClass}>
              {loadingTrend ? (
                <Skeleton className="h-full w-full" />
              ) : (
                <AppointmentsTrendChart points={trendPoints} height={288} />
              )}
            </CardContent>
          </Card>
          <UpcomingDaysStrip
            items={allAppointments}
            today={range.today}
            loading={loadingAppointments}
            layout="stack"
          />
        </div>
      ) : (
        <div className="mt-4 grid grid-cols-1 items-stretch gap-4 lg:grid-cols-5">
          <DashboardCalendarCard
            items={allAppointments}
            today={range.today}
            loading={loadingAppointments}
            className="lg:col-span-2"
          />
          <UpcomingDaysStrip
            items={allAppointments}
            today={range.today}
            loading={loadingAppointments}
            className="lg:col-span-3"
            layout="strip"
          />
        </div>
      )}

      <div
        className={cn(
          "mt-4 grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2",
          showRecalls ? "lg:grid-cols-4" : "lg:grid-cols-3",
        )}
      >
        <OutstandingCard
          total={outstanding?.total_outstanding ?? null}
          items={outstanding?.items ?? []}
          loading={loadingOutstanding}
        />
        {showRecalls ? (
          <RecallsCard
            items={recalls?.items ?? []}
            loading={role == null || loadingRecalls}
          />
        ) : null}
        <FailedRemindersCard
          items={failedReminders ?? []}
          loading={loadingReminders}
        />
        <OpenClaimsCard items={openClaims} loading={loadingClaims} />
      </div>

      <WalkInDialog
        open={walkInOpen}
        onOpenChange={setWalkInOpen}
        onDone={closeWalkIn}
      />
    </PageContainer>
  );
}
