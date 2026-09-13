import { Link } from "@tanstack/react-router";
import { Rows3 } from "lucide-react";
import type { WaitingRoomItem } from "@/lib/apiClient";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { ConnectionIndicator } from "@/features/waiting-room/components/ConnectionIndicator";
import { useRealtimeState } from "@/features/waiting-room/context/RealtimeContext";
import { formatTime } from "@/features/waiting-room/lib/waitingRoom";
import { cn } from "@/lib/utils";
import {
  dashboardCardClass,
  dashboardListBodyClass,
} from "../lib/dashboardLayout";
import { onFloor } from "../lib/dashboardStats";
import { DashboardCardHeader } from "./DashboardCardHeader";

const statusVariant: Record<string, "warning" | "brand" | "info" | "default"> =
  {
    Arrived: "warning",
    "In Consultation": "brand",
    Scheduled: "info",
  };

export function WaitingQueueCard({
  items,
  loading,
}: {
  items: WaitingRoomItem[];
  loading: boolean;
}) {
  const connectionState = useRealtimeState();
  const active = items.filter(onFloor);

  return (
    <Card className={dashboardCardClass}>
      <DashboardCardHeader
        title="Queue"
        to="/dashboard/waiting-room"
        extra={<ConnectionIndicator state={connectionState} />}
      />
      <CardContent
        className={cn(dashboardListBodyClass, "flex flex-col gap-0.5")}
      >
        {loading ? (
          <div className="flex flex-col gap-2 p-2">
            <Skeleton className="h-11 w-full" />
            <Skeleton className="h-11 w-full" />
            <Skeleton className="h-11 w-full" />
          </div>
        ) : active.length === 0 ? (
          <EmptyState
            icon={Rows3}
            heading="No one waiting"
            size="sm"
            className="m-auto py-4"
          />
        ) : (
          active.map((item) => {
            const status = item.current_visit_status ?? "Arrived";
            return (
              <Link
                key={item.id}
                to="/dashboard/waiting-room"
                className="flex min-h-11 items-center justify-between gap-2 rounded-lg px-2 py-2 text-sm native-press hover:bg-secondary"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium text-foreground">
                    {item.patient_name ?? "Patient"}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {formatTime(item.scheduled_start)}
                    {item.doctor_name ? ` · ${item.doctor_name}` : ""}
                  </p>
                </div>
                <Badge variant={statusVariant[status] ?? "default"} dot>
                  {status === "In Consultation" ? "In consult" : status}
                </Badge>
              </Link>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
