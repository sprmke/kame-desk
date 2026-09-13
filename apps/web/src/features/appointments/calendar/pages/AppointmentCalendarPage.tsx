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
import { doctorLabel } from "@/lib/doctorLabel";
import { ApiError } from "@/lib/apiError";
import { getClinicId } from "@/lib/auth";
import {
  appointmentToEvent,
  applyOptimisticMove,
  rollbackOptimisticMove,
  type CalendarEvent,
} from "@/features/appointments/calendar/lib/calendarEvents";
import { DOCTOR_CAT_COLORS } from "@/components/StatusIndicator";
import { SectionHeaderActions } from "@/components/layout/SectionHeaderActions";
import { AppointmentCalendarSkeleton } from "@/components/skeletons/PageSkeletons";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function AppointmentCalendarPage() {
  const clinicId = getClinicId()!;
  const qc = useQueryClient();
  const [doctorFilter, setDoctorFilter] = useState<string>("all");
  const [roomFilter, setRoomFilter] = useState<string>("all");
  const [layout, setLayout] = useState<"calendar" | "doctors">("calendar");
  const [colorByDoctor, setColorByDoctor] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [optimistic, setOptimistic] = useState<CalendarEvent[] | null>(null);

  const { data: clinic } = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => api.getClinic(clinicId),
  });

  const { data: doctors } = useQuery({
    queryKey: ["doctors", clinicId],
    queryFn: () => api.listDoctors(clinicId),
  });

  const { data: rooms } = useQuery({
    queryKey: ["rooms", clinicId],
    queryFn: () => api.listRooms(clinicId),
  });

  const { data: appointments, isLoading } = useQuery({
    queryKey: ["appointments", "calendar", doctorFilter, roomFilter],
    queryFn: () =>
      api.listAppointments({
        ...(doctorFilter !== "all" ? { doctor_id: doctorFilter } : {}),
        ...(roomFilter !== "all" ? { room_id: roomFilter } : {}),
      }),
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
    const doctorColors = new Map<string, string>();
    const palette = [...DOCTOR_CAT_COLORS];
    (doctors ?? []).forEach((d, i) => {
      doctorColors.set(d.id, palette[i % palette.length]);
    });
    return items.map((appt) => {
      const ev = appointmentToEvent(appt);
      if (colorByDoctor && doctorColors.has(appt.doctor_id)) {
        ev.backgroundColor = doctorColors.get(appt.doctor_id);
      }
      return ev;
    });
  }, [appointments, doctors, colorByDoctor]);

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
        <div className="flex items-center gap-2">
          <Label
            htmlFor="doctor-filter"
            className="text-xs text-muted-foreground"
          >
            Doctor
          </Label>
          <Select value={doctorFilter} onValueChange={setDoctorFilter}>
            <SelectTrigger id="doctor-filter" size="sm" className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {(doctors ?? []).map((d) => (
                <SelectItem key={d.id} value={d.id}>
                  {doctorLabel(d)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {(rooms ?? []).filter((r) => r.is_active).length > 0 && (
          <div className="flex items-center gap-2">
            <Label
              htmlFor="room-filter"
              className="text-xs text-muted-foreground"
            >
              Room
            </Label>
            <Select value={roomFilter} onValueChange={setRoomFilter}>
              <SelectTrigger id="room-filter" size="sm" className="w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {(rooms ?? [])
                  .filter((r) => r.is_active)
                  .map((r) => (
                    <SelectItem key={r.id} value={r.id}>
                      {r.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
        )}
        <Label className="flex items-center gap-2 text-sm text-foreground">
          <Switch
            checked={layout === "doctors"}
            onCheckedChange={(on) => setLayout(on ? "doctors" : "calendar")}
          />
          By doctor
        </Label>
        <Label className="flex items-center gap-2 text-sm text-foreground">
          <Switch checked={colorByDoctor} onCheckedChange={setColorByDoctor} />
          Color by doctor
        </Label>
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
      ) : layout === "doctors" ? (
        <div className="-mx-1 flex min-w-0 gap-3 overflow-x-auto pb-2">
          {(doctors ?? [])
            .filter((d) => doctorFilter === "all" || d.id === doctorFilter)
            .map((d) => (
              <div
                key={d.id}
                className="dd-calendar min-w-[280px] flex-1 rounded-2xl border border-border bg-card p-2 shadow-theme-xs sm:p-3"
              >
                <p className="mb-2 px-1 text-sm font-medium text-foreground">
                  {doctorLabel(d)}
                </p>
                <FullCalendar
                  plugins={[timeGridPlugin, interactionPlugin]}
                  initialView="timeGridDay"
                  headerToolbar={false}
                  height="auto"
                  editable
                  eventDrop={onEventDrop}
                  events={events.filter(
                    (ev) => ev.extendedProps.appointment.doctor_id === d.id,
                  )}
                  timeZone="Asia/Manila"
                  slotMinTime="07:00:00"
                  slotMaxTime="20:00:00"
                  allDaySlot={false}
                />
              </div>
            ))}
        </div>
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
