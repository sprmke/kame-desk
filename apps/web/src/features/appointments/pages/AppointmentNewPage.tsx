import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronLeft } from "lucide-react";
import { api } from "@/lib/apiClient";
import { doctorLabel } from "@/lib/doctorLabel";
import { ApiError } from "@/lib/apiError";
import { getClinicId } from "@/lib/auth";
import {
  appointmentFormSchema,
  type AppointmentFormValues,
} from "@/features/appointments/lib/schemas";
import {
  rruleFromPreset,
  type RecurrencePreset,
} from "@/features/appointments/lib/rrulePresets";
import {
  findConflictingAppointment,
  manilaSlotToUtc,
} from "@/features/appointments/lib/conflictCheck";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import { Input } from "@/components/ui/input";
import { Field, FieldError } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
import { Switch } from "@/components/ui/switch";
import { TimePicker } from "@/components/ui/time-picker";
import { Combobox } from "@/components/ui/combobox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PatientEligibilityCard } from "@/features/billing/components/PatientEligibilityCard";
import { useOnlineStatus } from "@/lib/onlineStatus";

type Props = { prefillPatientId?: string };

export function AppointmentNewPage({ prefillPatientId }: Props) {
  const clinicId = getClinicId()!;
  const navigate = useNavigate();
  const [clientConflict, setClientConflict] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [recurring, setRecurring] = useState(false);
  const [recurrence, setRecurrence] = useState<RecurrencePreset>("weekly");
  const [expansionNote, setExpansionNote] = useState<string | null>(null);

  const form = useForm<AppointmentFormValues>({
    resolver: zodResolver(appointmentFormSchema),
    defaultValues: {
      patient_id: prefillPatientId ?? "",
      doctor_id: "",
      room_id: "",
      service_fee_id: "",
      date: "",
      time: "10:00",
      duration_minutes: 30,
      reason_for_visit: "",
      notes: "",
    },
  });

  const { data: patients } = useQuery({
    queryKey: ["patients", "all"],
    queryFn: () => api.listPatients({ page_size: 100 }),
  });

  const { data: doctors } = useQuery({
    queryKey: ["doctors", clinicId],
    queryFn: () => api.listDoctors(clinicId),
  });

  const { data: rooms } = useQuery({
    queryKey: ["rooms", clinicId],
    queryFn: () => api.listRooms(clinicId),
  });

  const { data: fees } = useQuery({
    queryKey: ["service-fees", clinicId],
    queryFn: () => api.listServiceFees(clinicId),
  });

  const watchPatient = form.watch("patient_id");
  const watchDoctor = form.watch("doctor_id");
  const watchDate = form.watch("date");
  const watchTime = form.watch("time");
  const watchDuration = form.watch("duration_minutes");

  const doctorOptions = useMemo(
    () =>
      (doctors ?? []).map((d) => ({
        value: d.id,
        label: doctorLabel(d),
        keywords: d.specialty ?? undefined,
      })),
    [doctors],
  );

  const dayRange = useMemo(() => {
    if (!watchDate) return null;
    const start = new Date(`${watchDate}T00:00:00+08:00`);
    const end = new Date(`${watchDate}T23:59:59+08:00`);
    return {
      start_from: start.toISOString(),
      start_to: end.toISOString(),
    };
  }, [watchDate]);

  const { data: dayAppointments } = useQuery({
    queryKey: ["appointments", watchDoctor, watchDate],
    queryFn: () =>
      api.listAppointments({
        doctor_id: watchDoctor,
        ...dayRange!,
      }),
    enabled: Boolean(watchDoctor && dayRange),
  });

  useEffect(() => {
    if (!watchDoctor || !watchDate || !watchTime) {
      setClientConflict(null);
      return;
    }
    const { scheduled_start, scheduled_end } = manilaSlotToUtc(
      watchDate,
      watchTime,
      Number(watchDuration) || 30,
    );
    const conflict = findConflictingAppointment(
      dayAppointments?.items ?? [],
      watchDoctor,
      new Date(scheduled_start),
      new Date(scheduled_end),
    );
    setClientConflict(
      conflict
        ? `Conflicts with ${conflict.patient_name ?? "another patient"} at this time`
        : null,
    );
  }, [watchDoctor, watchDate, watchTime, watchDuration, dayAppointments]);

  const create = useMutation({
    mutationFn: async (values: AppointmentFormValues) => {
      const { scheduled_start, scheduled_end } = manilaSlotToUtc(
        values.date,
        values.time,
        values.duration_minutes,
      );
      if (recurring) {
        const result = await api.createAppointmentSeries({
          patient_id: values.patient_id,
          doctor_id: values.doctor_id,
          rrule_string: rruleFromPreset(recurrence, 12),
          series_start: scheduled_start,
          duration_minutes: values.duration_minutes,
          reason_for_visit: values.reason_for_visit || undefined,
        });
        const conflicts = result.expansion.conflicts.length;
        if (conflicts > 0) {
          setExpansionNote(`${conflicts} occurrence(s) could not be booked`);
        }
        return result.series;
      }
      return api.createAppointment({
        patient_id: values.patient_id,
        doctor_id: values.doctor_id,
        room_id: values.room_id || undefined,
        service_fee_id: values.service_fee_id || undefined,
        scheduled_start,
        scheduled_end,
        reason_for_visit: values.reason_for_visit || undefined,
        notes: values.notes || undefined,
      });
    },
    onSuccess: () => navigate({ to: "/dashboard/appointments" }),
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) {
        setServerError("This slot is no longer available");
      } else {
        setServerError(err instanceof Error ? err.message : "Booking failed");
      }
    },
  });

  const online = useOnlineStatus();
  const blocked = Boolean(clientConflict) || create.isPending || !online;

  return (
    <div className={pageContainerClass("narrow")}>
      <Link
        to="/dashboard/appointments"
        className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="size-4" />
        Appointments
      </Link>
      <PageHeader title="New appointment" />

      <Card>
        <CardContent className="pt-5">
          <form
            className="flex flex-col gap-4"
            onSubmit={form.handleSubmit((v) => {
              setServerError(null);
              create.mutate(v);
            })}
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor="patient_id" label="Patient" required />
                <Select
                  value={form.watch("patient_id")}
                  onValueChange={(value) => form.setValue("patient_id", value)}
                >
                  <SelectTrigger id="patient_id" className="w-full">
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {patients?.items.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.full_name} (#{p.patient_number})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FieldError>
                  {form.formState.errors.patient_id?.message}
                </FieldError>
              </Field>
              <Field>
                <FieldLabel htmlFor="doctor_id" label="Doctor" required />
                <Combobox
                  id="doctor_id"
                  value={form.watch("doctor_id")}
                  onValueChange={(value) => form.setValue("doctor_id", value)}
                  options={doctorOptions}
                  placeholder="Select doctor"
                  searchPlaceholder="Search doctors"
                />
                <FieldError>
                  {form.formState.errors.doctor_id?.message}
                </FieldError>
              </Field>
            </div>

            {(fees ?? []).length > 0 && (
              <Field>
                <FieldLabel htmlFor="service_fee_id" label="Type" />
                <Combobox
                  id="service_fee_id"
                  value={form.watch("service_fee_id") || ""}
                  onValueChange={(value) => {
                    form.setValue("service_fee_id", value);
                    const fee = fees?.find((f) => f.id === value);
                    if (fee?.duration_minutes) {
                      form.setValue("duration_minutes", fee.duration_minutes);
                    }
                  }}
                  options={(fees ?? []).map((f) => ({
                    value: f.id,
                    label: f.name,
                    keywords: f.category ?? undefined,
                  }))}
                  placeholder="Optional"
                  searchPlaceholder="Search services"
                />
              </Field>
            )}

            {(rooms ?? []).filter((r) => r.is_active).length > 0 && (
              <Field>
                <FieldLabel htmlFor="room_id" label="Room" />
                <Select
                  value={form.watch("room_id") || ""}
                  onValueChange={(value) => form.setValue("room_id", value)}
                >
                  <SelectTrigger id="room_id" className="w-full">
                    <SelectValue placeholder="Optional" />
                  </SelectTrigger>
                  <SelectContent>
                    {(rooms ?? [])
                      .filter((r) => r.is_active)
                      .map((r) => (
                        <SelectItem key={r.id} value={r.id}>
                          {r.name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </Field>
            )}

            <div className="grid gap-4 sm:grid-cols-3">
              <Field>
                <FieldLabel htmlFor="date" label="Date" required />
                <DatePicker
                  id="date"
                  {...form.register("date")}
                  value={watchDate}
                />
                <FieldError>{form.formState.errors.date?.message}</FieldError>
              </Field>
              <Field>
                <FieldLabel htmlFor="time" label="Time (Manila)" required />
                <TimePicker
                  id="time"
                  {...form.register("time")}
                  value={watchTime}
                />
                <FieldError>{form.formState.errors.time?.message}</FieldError>
              </Field>
              <Field>
                <FieldLabel
                  htmlFor="duration_minutes"
                  label="Duration (min)"
                  required
                />
                <Input
                  id="duration_minutes"
                  type="number"
                  min={5}
                  {...form.register("duration_minutes")}
                />
                <FieldError>
                  {form.formState.errors.duration_minutes?.message}
                </FieldError>
              </Field>
            </div>

            <Field>
              <FieldLabel htmlFor="reason_for_visit" label="Reason" />
              <Input
                id="reason_for_visit"
                placeholder={FORM_PLACEHOLDERS.reasonForVisit}
                {...form.register("reason_for_visit")}
              />
            </Field>

            <label className="flex items-center gap-2.5 text-sm text-foreground">
              <Switch checked={recurring} onCheckedChange={setRecurring} />
              Recurring
            </label>

            {recurring && (
              <Select
                value={recurrence}
                onValueChange={(value) =>
                  setRecurrence(value as RecurrencePreset)
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="biweekly">Every 2 weeks</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            )}

            {expansionNote && (
              <p className="text-sm text-warning">{expansionNote}</p>
            )}
            {clientConflict && (
              <p className="text-sm text-warning">{clientConflict}</p>
            )}
            {serverError && (
              <p className="text-sm text-destructive">{serverError}</p>
            )}
            {!online && (
              <p className="text-sm text-warning">
                Booking requires a connection. Reconnect to continue.
              </p>
            )}

            <Button type="submit" className="w-fit" disabled={blocked}>
              {create.isPending ? "Booking…" : "Book"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {watchPatient && (
        <div className="mt-4">
          <PatientEligibilityCard patientId={watchPatient} />
        </div>
      )}
    </div>
  );
}
