export type VisitColumn =
  "Scheduled" | "Arrived" | "In Consultation" | "Completed";

export type WaitingRoomItem = {
  id: string;
  patient_id: string;
  patient_name?: string | null;
  doctor_id: string;
  doctor_name?: string | null;
  scheduled_start: string;
  scheduled_end: string;
  appointment_status: string;
  current_visit_status: string | null;
  reason_for_visit?: string | null;
};

export function columnForItem(item: WaitingRoomItem): VisitColumn {
  if (!item.current_visit_status) return "Scheduled";
  return item.current_visit_status as VisitColumn;
}

export function nextVisitStatus(
  current: string | null,
): "Arrived" | "In Consultation" | "Completed" | null {
  if (!current) return "Arrived";
  if (current === "Arrived") return "In Consultation";
  if (current === "In Consultation") return "Completed";
  return null;
}

export function columnToVisitStatus(
  column: VisitColumn,
): "Arrived" | "In Consultation" | "Completed" | null {
  if (column === "Scheduled") return null;
  return column;
}

export function canDropToColumn(
  current: string | null,
  targetColumn: VisitColumn,
): boolean {
  const target = columnToVisitStatus(targetColumn);
  if (!target) return false;
  return nextVisitStatus(current) === target;
}

export function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-PH", {
    timeZone: "Asia/Manila",
    hour: "numeric",
    minute: "2-digit",
  });
}
