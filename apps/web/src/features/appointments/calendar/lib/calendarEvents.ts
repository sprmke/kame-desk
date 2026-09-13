import type { Appointment } from "@/lib/apiClient";
import { CALENDAR_STATUS_COLOR } from "@/components/StatusIndicator";

export type CalendarEvent = {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor?: string;
  extendedProps: {
    appointment: Appointment;
  };
};

export function appointmentToEvent(appt: Appointment): CalendarEvent {
  const label = appt.patient_name ?? "Patient";
  return {
    id: appt.id,
    title: `${label}${appt.doctor_name ? ` · ${appt.doctor_name}` : ""}`,
    start: appt.scheduled_start,
    end: appt.scheduled_end,
    backgroundColor:
      CALENDAR_STATUS_COLOR[appt.appointment_status] ??
      "var(--status-scheduled)",
    extendedProps: { appointment: appt },
  };
}

export function applyOptimisticMove(
  events: CalendarEvent[],
  eventId: string,
  start: Date,
  end: Date,
): CalendarEvent[] {
  return events.map((ev) =>
    ev.id === eventId
      ? { ...ev, start: start.toISOString(), end: end.toISOString() }
      : ev,
  );
}

export function rollbackOptimisticMove(
  events: CalendarEvent[],
  eventId: string,
  prior: { start: string; end: string },
): CalendarEvent[] {
  return events.map((ev) =>
    ev.id === eventId ? { ...ev, start: prior.start, end: prior.end } : ev,
  );
}
