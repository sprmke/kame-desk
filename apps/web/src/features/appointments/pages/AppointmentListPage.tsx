import { Link } from "@tanstack/react-router";
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { CalendarDays, CalendarPlus, Notebook } from "lucide-react";
import { api, type Appointment } from "@/lib/apiClient";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { getClinicId } from "@/lib/auth";
import { doctorLabel } from "@/lib/doctorLabel";
import { DatePicker, DateRangePicker } from "@/components/ui/date-picker";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AppointmentRowActions,
  useAppointmentRowActions,
} from "@/features/appointments/components/AppointmentRowActions";
import { SeriesScopeDialog } from "@/features/appointments/components/SeriesScopeDialog";
import { AppointmentCalendarBoard } from "@/features/appointments/calendar/components/AppointmentCalendarBoard";
import { SectionHeaderActions } from "@/components/layout/SectionHeaderActions";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusIndicator } from "@/components/StatusIndicator";
import { EmptyState } from "@/components/EmptyState";
import { AppointmentListSkeleton } from "@/components/skeletons/PageSkeletons";
import {
  SwipeRevealRow,
  type SwipeRevealAction,
} from "@/components/mobile/SwipeRevealRow";
import { useIsBelowLg, usePrefersReducedMotion } from "@/hooks/useMediaQuery";
import { useListSearch } from "@/hooks/useListSearch";
import { PatientCombobox } from "@/features/patients/components/PatientCombobox";
import {
  ListSortHeader,
  ListStack,
  ListTableShell,
  ManagedList,
} from "@/components/list";
import type { ListViewMode } from "@/lib/list/viewMode";

function formatManila(iso: string) {
  return new Date(iso).toLocaleString("en-PH", {
    timeZone: "Asia/Manila",
    dateStyle: "medium",
    timeStyle: "short",
  });
}

const APPOINTMENT_VIEWS: ListViewMode[] = ["table", "list", "calendar"];
const APPOINTMENT_EXTRA = ["status", "doctorId", "from", "to"] as const;
const APPOINTMENT_SORTS = [
  { value: "start:asc", label: "Soonest" },
  { value: "start:desc", label: "Latest" },
  { value: "patient:asc", label: "Patient A-Z" },
  { value: "status:asc", label: "Status" },
  { value: "created_at:desc", label: "Newest" },
] as const;

function AppointmentRowBody({
  appointment,
  extra,
}: {
  appointment: Appointment;
  extra?: ReactNode;
}) {
  return (
    <div className="bg-card px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium text-foreground">
            {appointment.patient_name ?? "Patient"} ·{" "}
            {appointment.doctor_name ?? "Doctor"}
          </p>
          <p className="text-sm text-muted-foreground">
            {formatManila(appointment.scheduled_start)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusIndicator status={appointment.appointment_status} />
          {(appointment.booking_source === "public_link" ||
            appointment.booking_source === "public_assistant") && (
            <Badge variant="info">Public</Badge>
          )}
          {appointment.no_show_risk?.level === "high" && (
            <Badge variant="warning">No-show risk</Badge>
          )}
        </div>
      </div>
      {appointment.reason_for_visit && (
        <p className="mt-1 text-sm text-muted-foreground">
          {appointment.reason_for_visit}
        </p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <Button asChild variant="ghost" size="sm">
          <Link
            to="/dashboard/appointments/$appointmentId/soap"
            params={{ appointmentId: appointment.id }}
          >
            <Notebook className="size-4" />
            SOAP
          </Link>
        </Button>
        {extra}
      </div>
    </div>
  );
}

function SwipeAppointmentRow({ appointment }: { appointment: Appointment }) {
  const actions = useAppointmentRowActions(appointment);
  const swipeActions: SwipeRevealAction[] = [];
  if (actions.canCancel) {
    swipeActions.push({
      key: "cancel",
      label: "Cancel",
      variant: "destructive",
      onClick: actions.onCancel,
    });
  }
  if (actions.canNoShow) {
    swipeActions.push({
      key: "noshow",
      label: "No show",
      variant: "outline",
      onClick: actions.onNoShow,
    });
  }

  const body = <AppointmentRowBody appointment={appointment} />;
  return (
    <>
      {swipeActions.length > 0 ? (
        <SwipeRevealRow actions={swipeActions}>{body}</SwipeRevealRow>
      ) : (
        body
      )}
      <SeriesScopeDialog
        open={actions.scopeOpen}
        action="cancel"
        hasSeries={actions.hasSeries}
        onChoose={actions.chooseScope}
        onClose={() => actions.setScopeOpen(false)}
      />
    </>
  );
}

export function AppointmentListPage() {
  const clinicId = getClinicId()!;
  const qc = useQueryClient();
  const list = useListSearch({
    defaultSort: "start:asc",
    views: APPOINTMENT_VIEWS,
    extraKeys: APPOINTMENT_EXTRA,
  });
  const status = list.extras.status || "all";
  const doctorId = list.extras.doctorId || "all";
  const fromDate = list.extras.from;
  const toDate = list.extras.to;
  const isCalendar = list.view === "calendar";

  const { data: doctors } = useQuery({
    queryKey: ["doctors", clinicId],
    queryFn: () => api.listDoctors(clinicId),
  });

  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: [
      "appointments",
      list.q,
      status,
      doctorId,
      fromDate,
      toDate,
      list.page,
      list.limit,
      list.sort,
      isCalendar,
    ],
    queryFn: () =>
      api.listAppointments({
        q: list.q || undefined,
        status: status === "all" ? undefined : status,
        doctor_id: doctorId === "all" ? undefined : doctorId,
        start_from: fromDate
          ? new Date(`${fromDate}T00:00:00+08:00`).toISOString()
          : undefined,
        start_to: toDate
          ? new Date(`${toDate}T23:59:59+08:00`).toISOString()
          : undefined,
        sort: list.sort,
        ...(isCalendar ? {} : { page: list.page, page_size: list.limit }),
      }),
    placeholderData: keepPreviousData,
  });

  const { data: publicRequests } = useQuery({
    queryKey: ["appointments", "public-requests"],
    queryFn: () =>
      api.listAppointments({
        booking_source: "public_link",
        status: "Scheduled",
      }),
  });

  const { data: waitlist } = useQuery({
    queryKey: ["waitlist"],
    queryFn: () => api.listWaitlist({ status: "waiting" }),
  });

  const confirmPublic = useMutation({
    mutationFn: (id: string) =>
      api.patchAppointment(id, { appointment_status: "Confirmed" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["appointments"] });
    },
  });

  const [waitPatient, setWaitPatient] = useState("");
  const [waitDoctor, setWaitDoctor] = useState("any");
  const [waitDate, setWaitDate] = useState("");

  const addWaitlist = useMutation({
    mutationFn: () =>
      api.createWaitlist({
        patient_id: waitPatient,
        doctor_id: waitDoctor === "any" ? undefined : waitDoctor,
        preferred_date: waitDate || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["waitlist"] });
      setWaitPatient("");
      setWaitDate("");
    },
  });

  const dropWaitlist = useMutation({
    mutationFn: (id: string) => api.patchWaitlist(id, { status: "cancelled" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["waitlist"] }),
  });

  const isBelowLg = useIsBelowLg();
  const reducedMotion = usePrefersReducedMotion();
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const refineCount =
    (status !== "all" ? 1 : 0) +
    (doctorId !== "all" ? 1 : 0) +
    (fromDate || toDate ? 1 : 0);

  const statusSelect = (
    <Select
      value={status}
      onValueChange={(value) => list.setParams({ status: value, page: 1 })}
    >
      <SelectTrigger
        className="h-10 min-h-[44px] w-full min-w-[9rem] lg:min-h-10"
        aria-label="Status"
      >
        <SelectValue placeholder="Status" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All statuses</SelectItem>
        <SelectItem value="Scheduled">Scheduled</SelectItem>
        <SelectItem value="Confirmed">Confirmed</SelectItem>
        <SelectItem value="Cancelled">Cancelled</SelectItem>
        <SelectItem value="No Show">No Show</SelectItem>
      </SelectContent>
    </Select>
  );

  const refineFilters = (
    <>
      <div className="flex flex-col gap-1.5">
        <Label>Doctor</Label>
        <Select
          value={doctorId}
          onValueChange={(value) =>
            list.setParams({ doctorId: value, page: 1 })
          }
        >
          <SelectTrigger className="w-full">
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
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="appointment-date-range">Date range</Label>
        <DateRangePicker
          id="appointment-date-range"
          from={fromDate}
          to={toDate}
          onValueChange={(range) => list.setParams({ ...range, page: 1 })}
        />
      </div>
    </>
  );

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

      {(publicRequests?.items ?? []).length > 0 && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Public requests</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col divide-y divide-border text-sm">
              {publicRequests?.items.map((a) => (
                <li
                  key={a.id}
                  className="flex flex-wrap items-center justify-between gap-2 py-2 first:pt-0 last:pb-0"
                >
                  <span>
                    {a.patient_name ?? "Patient"} · {a.doctor_name ?? "Doctor"}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={confirmPublic.isPending}
                    onClick={() => confirmPublic.mutate(a.id)}
                  >
                    Confirm
                  </Button>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Waitlist</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <form
            className="grid gap-2 sm:grid-cols-[2fr_1fr_1fr_auto] sm:items-end"
            onSubmit={(e) => {
              e.preventDefault();
              if (!waitPatient) return;
              addWaitlist.mutate();
            }}
          >
            <PatientCombobox
              value={waitPatient}
              onValueChange={setWaitPatient}
              disabled={addWaitlist.isPending}
            />
            <Select value={waitDoctor} onValueChange={setWaitDoctor}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any doctor</SelectItem>
                {(doctors ?? []).map((d) => (
                  <SelectItem key={d.id} value={d.id}>
                    {doctorLabel(d)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <DatePicker value={waitDate} onValueChange={setWaitDate} />
            <Button type="submit" size="sm" disabled={addWaitlist.isPending}>
              Add
            </Button>
          </form>
          {(waitlist ?? []).length === 0 ? (
            <EmptyState
              icon={CalendarDays}
              heading="No waitlist entries"
              size="sm"
            />
          ) : (
            <ul className="flex flex-col divide-y divide-border text-sm">
              {waitlist?.map((w) => (
                <li
                  key={w.id}
                  className="flex flex-wrap items-center justify-between gap-2 py-2 first:pt-0 last:pb-0"
                >
                  <span>
                    {w.patient_name ?? "Patient"}
                    {w.doctor_name ? ` · ${w.doctor_name}` : ""}
                    {w.preferred_date ? ` · ${w.preferred_date}` : ""}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => dropWaitlist.mutate(w.id)}
                  >
                    Remove
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <ManagedList
        entityLabel="appointments"
        total={total}
        page={list.page}
        limit={list.limit}
        view={list.view}
        views={APPOINTMENT_VIEWS}
        onViewChange={list.setView}
        onPageChange={list.setPage}
        onLimitChange={list.setLimit}
        sort={list.sort}
        sortOptions={APPOINTMENT_SORTS}
        onSortChange={list.setSort}
        searchPlaceholder={FORM_PLACEHOLDERS.searchAppointments}
        searchValue={list.q}
        onSearchChange={list.setQuery}
        leading={statusSelect}
        refine={refineFilters}
        refineCount={refineCount}
        onClearFilters={() =>
          list.setParams({
            status: undefined,
            doctorId: undefined,
            from: undefined,
            to: undefined,
            page: 1,
          })
        }
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        onRetry={() => refetch()}
        hidePagination={isCalendar}
        hideTableView={list.hideTableView}
        empty={<EmptyState icon={CalendarDays} heading="No appointments" />}
      >
        {isLoading ? (
          <ListTableShell>
            <AppointmentListSkeleton />
          </ListTableShell>
        ) : isCalendar ? (
          <AppointmentCalendarBoard appointments={items} />
        ) : list.view === "table" ? (
          <ListTableShell>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <ListSortHeader
                      label="When"
                      column="start"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>
                    <ListSortHeader
                      label="Patient"
                      column="patient"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>Doctor</TableHead>
                  <TableHead>
                    <ListSortHeader
                      label="Status"
                      column="status"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="text-muted-foreground">
                      {formatManila(a.scheduled_start)}
                    </TableCell>
                    <TableCell className="font-medium text-foreground">
                      {a.patient_name ?? "Patient"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {a.doctor_name ?? "Doctor"}
                    </TableCell>
                    <TableCell>
                      <StatusIndicator status={a.appointment_status} />
                    </TableCell>
                    <TableCell>
                      <AppointmentRowActions appointment={a} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ListTableShell>
        ) : (
          <ListStack>
            {items.map((a) => (
              <li key={a.id} className="native-press">
                {isBelowLg && !reducedMotion ? (
                  <SwipeAppointmentRow appointment={a} />
                ) : (
                  <AppointmentRowBody
                    appointment={a}
                    extra={<AppointmentRowActions appointment={a} />}
                  />
                )}
              </li>
            ))}
          </ListStack>
        )}
      </ManagedList>
    </div>
  );
}
