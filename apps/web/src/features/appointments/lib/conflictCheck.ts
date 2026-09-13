import type { Appointment } from "@/lib/apiClient";

const INACTIVE_STATUSES = new Set(["Cancelled", "No Show", "Rescheduled"]);

export function rangesOverlap(
  startA: Date,
  endA: Date,
  startB: Date,
  endB: Date,
): boolean {
  return startA < endB && startB < endA;
}

export function findConflictingAppointment(
  appointments: Appointment[],
  doctorId: string,
  start: Date,
  end: Date,
  excludeId?: string,
): Appointment | undefined {
  return appointments.find((appt) => {
    if (appt.id === excludeId) return false;
    if (appt.doctor_id !== doctorId) return false;
    if (INACTIVE_STATUSES.has(appt.appointment_status)) return false;
    const apptStart = new Date(appt.scheduled_start);
    const apptEnd = new Date(appt.scheduled_end);
    return rangesOverlap(start, end, apptStart, apptEnd);
  });
}

/** Wall-clock date/time in Asia/Manila → UTC ISO strings for API. */
export function manilaSlotToUtc(
  date: string,
  time: string,
  durationMinutes: number,
): { scheduled_start: string; scheduled_end: string } {
  const start = new Date(`${date}T${time}:00+08:00`);
  const end = new Date(start.getTime() + durationMinutes * 60_000);
  return {
    scheduled_start: start.toISOString(),
    scheduled_end: end.toISOString(),
  };
}
