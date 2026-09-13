import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { EventDropArg } from "@fullcalendar/core";
import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type Appointment } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import {
  appointmentToEvent,
  applyOptimisticMove,
  rollbackOptimisticMove,
  type CalendarEvent,
} from "@/features/appointments/calendar/lib/calendarEvents";

export function AppointmentCalendarBoard({
  appointments,
}: {
  appointments: Appointment[];
}) {
  const qc = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [optimistic, setOptimistic] = useState<CalendarEvent[] | null>(null);

  const baseEvents = useMemo(
    () => appointments.map((appt) => appointmentToEvent(appt)),
    [appointments],
  );
  const events = optimistic ?? baseEvents;

  const reschedule = useMutation({
    mutationFn: ({
      id,
      start,
      end,
    }: {
      id: string;
      start: string;
      end: string;
    }) =>
      api.rescheduleAppointment(id, {
        scheduled_start: start,
        scheduled_end: end,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["appointments"] });
      setOptimistic(null);
      setError(null);
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Reschedule failed");
    },
  });

  function onEventDrop(info: EventDropArg) {
    const prior = {
      start: info.oldEvent.start!.toISOString(),
      end: info.oldEvent.end!.toISOString(),
    };
    const nextStart = info.event.start!.toISOString();
    const nextEnd = info.event.end!.toISOString();
    setOptimistic(
      applyOptimisticMove(
        baseEvents,
        info.event.id,
        info.event.start!,
        info.event.end!,
      ),
    );
    reschedule.mutate(
      { id: info.event.id, start: nextStart, end: nextEnd },
      {
        onError: () => {
          setOptimistic(
            rollbackOptimisticMove(baseEvents, info.event.id, prior),
          );
          info.revert();
        },
      },
    );
  }

  return (
    <div className="dd-calendar rounded-2xl border border-border bg-card p-2 shadow-theme-xs sm:p-4">
      {error ? <p className="mb-2 text-sm text-destructive">{error}</p> : null}
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        headerToolbar={{
          left: "prev,next today",
          center: "title",
          right: "dayGridMonth,timeGridWeek,timeGridDay",
        }}
        height="auto"
        editable
        eventDrop={onEventDrop}
        events={events}
        timeZone="Asia/Manila"
      />
    </div>
  );
}
