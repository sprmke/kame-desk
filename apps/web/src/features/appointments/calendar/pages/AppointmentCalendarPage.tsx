import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { EventDropArg } from "@fullcalendar/core";
import { useMemo, useState } from "react";
import { CalendarPlus, ExternalLink } from "lucide-react";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import { getClinicId } from "@/lib/auth";
import {
  appointmentToEvent,
  applyOptimisticMove,
  rollbackOptimisticMove,
  type CalendarEvent,
} from "@/features/appointments/calendar/lib/calendarEvents";
import { SectionHeaderActions } from "@/components/layout/SectionHeaderActions";
import { AppointmentCalendarSkeleton } from "@/components/skeletons/PageSkeletons";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

export function AppointmentCalendarPage() {
  const clinicId = getClinicId()!;
  const qc = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [optimistic, setOptimistic] = useState<CalendarEvent[] | null>(null);

  const { data: clinic } = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => api.getClinic(clinicId),
  });

  const { data: appointments, isLoading } = useQuery({
    queryKey: ["appointments", "calendar"],
    queryFn: () => api.listAppointments(),
  });

  const patchClinic = useMutation({
    mutationFn: (body: { public_booking_auto_confirm: boolean }) =>
      api.patchClinic(clinicId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clinic", clinicId] }),
  });

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

  const baseEvents = useMemo(() => {
    const items = appointments?.items ?? [];
    return items.map((appt) => appointmentToEvent(appt));
  }, [appointments]);

  const events = optimistic ?? baseEvents;

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
    <div>
      <SectionHeaderActions>
        <Button asChild>
          <Link
            to="/dashboard/appointments/new"
            search={{ patientId: undefined }}
          >
            <CalendarPlus className="size-4" />
            New appointment
          </Link>
        </Button>
      </SectionHeaderActions>

      <div className="mb-4 flex flex-wrap items-center gap-4 rounded-xl border border-border bg-card px-4 py-3 shadow-theme-xs">
        {clinic && (
          <Label className="flex items-center gap-2 text-sm text-foreground">
            <Switch
              checked={clinic.public_booking_auto_confirm}
              onCheckedChange={(checked) =>
                patchClinic.mutate({ public_booking_auto_confirm: checked })
              }
            />
            Auto-confirm public bookings
          </Label>
        )}
        {clinic?.slug && (
          <Link
            to="/book/$slug"
            params={{ slug: clinic.slug }}
            className="ml-auto inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
            target="_blank"
          >
            Public link
            <ExternalLink className="size-3.5" />
          </Link>
        )}
      </div>

      {error && <p className="mb-2 text-sm text-destructive">{error}</p>}

      {isLoading ? (
        <AppointmentCalendarSkeleton />
      ) : (
        <div className="dd-calendar rounded-2xl border border-border bg-card p-2 shadow-theme-xs sm:p-4">
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
      )}
    </div>
  );
}
