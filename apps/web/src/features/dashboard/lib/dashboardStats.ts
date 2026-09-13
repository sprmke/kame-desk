import type { Appointment, WaitingRoomItem } from "@/lib/apiClient";
import { manilaDateFromTimestamp } from "./dashboardRange";

const TERMINAL_APPOINTMENT = new Set(["Cancelled", "No Show", "Rescheduled"]);

export function appointmentsOnDate(
  items: Appointment[],
  isoDate: string,
): Appointment[] {
  return items
    .filter((item) => manilaDateFromTimestamp(item.scheduled_start) === isoDate)
    .sort(
      (a, b) =>
        new Date(a.scheduled_start).getTime() -
        new Date(b.scheduled_start).getTime(),
    );
}

export function isActiveAppointment(item: Appointment) {
  return !TERMINAL_APPOINTMENT.has(item.appointment_status);
}

export function activeAppointmentCount(items: Appointment[]) {
  return items.filter(isActiveAppointment).length;
}

export function onFloor(item: { current_visit_status?: string | null }) {
  return (
    item.current_visit_status === "Arrived" ||
    item.current_visit_status === "In Consultation"
  );
}

export function waitingNowCount(items: WaitingRoomItem[]) {
  return items.filter(onFloor).length;
}

/** Appointments not currently in the waiting-room floor (avoids Today/Queue duplicates). */
export function notOnFloor(item: Appointment) {
  return !onFloor(item);
}

export function scheduledWaitingCount(items: WaitingRoomItem[]) {
  return items.filter((item) => !item.current_visit_status).length;
}

export function completedVisitCount(items: WaitingRoomItem[]) {
  return items.filter((item) => item.current_visit_status === "Completed")
    .length;
}

export function nextAppointmentId(
  items: Appointment[],
  now = new Date(),
): string | null {
  const upcoming = items.find(
    (item) =>
      isActiveAppointment(item) &&
      item.current_visit_status !== "Completed" &&
      new Date(item.scheduled_start).getTime() >= now.getTime(),
  );
  if (upcoming) return upcoming.id;
  const inProgress = items.find(
    (item) =>
      isActiveAppointment(item) && item.current_visit_status !== "Completed",
  );
  return inProgress?.id ?? null;
}

export function bookedDates(items: Appointment[]): Date[] {
  const seen = new Set<string>();
  const dates: Date[] = [];
  for (const item of items) {
    if (!isActiveAppointment(item)) continue;
    const iso = manilaDateFromTimestamp(item.scheduled_start);
    if (seen.has(iso)) continue;
    seen.add(iso);
    const [year, month, day] = iso.split("-").map(Number);
    dates.push(new Date(year, month - 1, day));
  }
  return dates;
}

export function groupUpcomingByDay(
  items: Appointment[],
  today: string,
  throughDate: string,
) {
  const groups: Array<{ date: string; items: Appointment[] }> = [];
  const byDay = new Map<string, Appointment[]>();
  for (const item of items) {
    if (!isActiveAppointment(item)) continue;
    const date = manilaDateFromTimestamp(item.scheduled_start);
    if (date <= today || date > throughDate) continue;
    const list = byDay.get(date) ?? [];
    list.push(item);
    byDay.set(date, list);
  }
  for (const [date, dayItems] of [...byDay.entries()].sort(([a], [b]) =>
    a.localeCompare(b),
  )) {
    groups.push({
      date,
      items: dayItems.sort(
        (a, b) =>
          new Date(a.scheduled_start).getTime() -
          new Date(b.scheduled_start).getTime(),
      ),
    });
  }
  return groups;
}

export const OPEN_CLAIM_STATUSES = new Set(["draft", "submitted"]);

export function visitOrAppointmentStatus(item: {
  appointment_status: string;
  current_visit_status?: string | null;
}) {
  return item.current_visit_status || item.appointment_status;
}
