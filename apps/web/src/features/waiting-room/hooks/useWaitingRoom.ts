import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import type { WaitingRoomItem } from "../lib/waitingRoom";

export function useWaitingRoom() {
  return useQuery({
    queryKey: ["waiting-room"],
    queryFn: () => api.getWaitingRoom(),
    refetchInterval: false,
  });
}

export function useAdvanceVisitStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      appointmentId,
      visitStatus,
    }: {
      appointmentId: string;
      visitStatus: "Arrived" | "In Consultation" | "Completed";
    }) => api.updateVisitStatus(appointmentId, visitStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["waiting-room"] });
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
    },
  });
}

export function groupByColumn(items: WaitingRoomItem[]) {
  const columns: Record<string, WaitingRoomItem[]> = {
    Scheduled: [],
    Arrived: [],
    "In Consultation": [],
    Completed: [],
  };
  for (const item of items) {
    const key = item.current_visit_status ?? "Scheduled";
    if (columns[key]) columns[key].push(item);
    else columns.Scheduled.push(item);
  }
  return columns;
}
