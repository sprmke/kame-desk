import { Link } from "@tanstack/react-router";
import {
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  Rows3,
} from "lucide-react";
import { StatCard } from "@/components/StatCard";
import { Skeleton } from "@/components/ui/skeleton";
import { formatPhp } from "../lib/dashboardRange";

type Props = {
  todayCount: number | null;
  waitingCount: number | null;
  scheduledWaiting: number | null;
  completedCount: number | null;
  monthRevenue: string | null;
  todayRevenue: string | null;
  weekRevenue: string | null;
  loadingToday: boolean;
  loadingWaiting: boolean;
  loadingRevenue: boolean;
};

export function DashboardKpiRow({
  todayCount,
  waitingCount,
  scheduledWaiting,
  completedCount,
  monthRevenue,
  todayRevenue,
  weekRevenue,
  loadingToday,
  loadingWaiting,
  loadingRevenue,
}: Props) {
  const waitingHint =
    scheduledWaiting && scheduledWaiting > 0
      ? `${scheduledWaiting} scheduled`
      : undefined;

  return (
    <div className="grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Link
        to="/dashboard/appointments"
        className="block h-full min-w-0 rounded-lg native-press"
      >
        <StatCard
          label="Today"
          value={
            loadingToday ? <Skeleton className="h-8 w-12" /> : (todayCount ?? 0)
          }
          icon={CalendarDays}
          tone="brand"
        />
      </Link>
      <Link
        to="/dashboard/waiting-room"
        className="block h-full min-w-0 rounded-lg native-press"
      >
        <StatCard
          label="Waiting"
          value={
            loadingWaiting ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              (waitingCount ?? 0)
            )
          }
          hint={waitingHint}
          icon={Rows3}
          tone="warning"
        />
      </Link>
      <Link
        to="/dashboard/waiting-room"
        className="block h-full min-w-0 rounded-lg native-press"
      >
        <StatCard
          label="Completed"
          value={
            loadingWaiting ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              (completedCount ?? 0)
            )
          }
          icon={CheckCircle2}
          tone="success"
        />
      </Link>
      <Link
        to="/dashboard/billing/invoices"
        className="block h-full min-w-0 rounded-lg native-press"
      >
        <StatCard
          label="Revenue"
          value={
            loadingRevenue ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              formatPhp(monthRevenue)
            )
          }
          hint={
            todayRevenue != null && weekRevenue != null
              ? `Today ${formatPhp(todayRevenue)} · Week ${formatPhp(weekRevenue)}`
              : undefined
          }
          icon={CircleDollarSign}
          tone="info"
        />
      </Link>
    </div>
  );
}
