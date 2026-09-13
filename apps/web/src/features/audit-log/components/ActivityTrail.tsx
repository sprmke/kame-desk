import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ActivityTrailSkeleton } from "@/components/skeletons/PageSkeletons";
import { EmptyState } from "@/components/EmptyState";

type Props = {
  targetType?: string;
  targetId?: string;
  title?: string;
};

export function ActivityTrail({
  targetType,
  targetId,
  title = "Activity",
}: Props) {
  const clinicId = getClinicId();
  const { data, isLoading } = useQuery({
    queryKey: ["activity-log", clinicId, targetType, targetId],
    queryFn: () =>
      api.listActivityLog(clinicId!, {
        target_type: targetType,
        target_id: targetId,
        page_size: 20,
      }),
    enabled: Boolean(clinicId),
  });

  const items = data?.items ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <History className="size-4 text-muted-foreground" />
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <ActivityTrailSkeleton />
        ) : items.length === 0 ? (
          <EmptyState
            icon={History}
            heading="No activity yet"
            className="py-8"
          />
        ) : (
          <ul className="flex flex-col divide-y divide-border">
            {items.map((row) => (
              <li key={row.id} className="py-2.5 text-sm first:pt-0 last:pb-0">
                <p className="text-foreground">{row.summary}</p>
                <p className="text-xs text-muted-foreground">
                  {row.actor_name ?? row.actor_type} ·{" "}
                  {new Date(row.created_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
