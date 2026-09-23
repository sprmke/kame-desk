import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { CalendarCheck } from "lucide-react";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { addDaysIso, todayIsoManila } from "@/lib/isoDate";
import { normalizePublicIntake } from "@/lib/publicIntake";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { PublicBookingSkeleton } from "@/components/skeletons/PageSkeletons";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type Props = { slug: string };

type Slot = { scheduled_start: string; scheduled_end: string };

function formatSlot(start: string) {
  return new Date(start).toLocaleString("en-PH", {
    timeZone: "Asia/Manila",
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function PublicBookingPage({ slug }: Props) {
  const [doctorId, setDoctorId] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [date, setDate] = useState("");
  const [slot, setSlot] = useState<Slot | null>(null);
  const [fullName, setFullName] = useState("");
  const [contact, setContact] = useState("");
  const [email, setEmail] = useState("");
  const [birthdate, setBirthdate] = useState("");
  const [sex, setSex] = useState("");
  const [address, setAddress] = useState("");
  const [reason, setReason] = useState("");
  const [existing, setExisting] = useState("");
  const [notes, setNotes] = useState("");
  const [done, setDone] = useState(false);
  const [confirmed, setConfirmed] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { data: clinic, isLoading } = useQuery({
    queryKey: ["public-clinic", slug],
    queryFn: () => api.getPublicClinic(slug),
  });

  const intake = normalizePublicIntake(clinic?.public_intake_fields);
  const services = clinic?.services ?? [];
  const selectedService = services.find((item) => item.id === serviceId);
  const durationMinutes =
    selectedService?.duration_minutes ??
    clinic?.default_appointment_duration_minutes;
  const today = todayIsoManila();
  const maxDate = clinic
    ? addDaysIso(today, clinic.advance_booking_days || 90)
    : undefined;

  useEffect(() => {
    if (!clinic?.doctors.length) return;
    if (clinic.doctors.length === 1) {
      setDoctorId(clinic.doctors[0].id);
    }
  }, [clinic]);

  const { data: slots, isFetching } = useQuery({
    queryKey: ["public-slots", slug, doctorId, date, durationMinutes],
    queryFn: () => api.getPublicSlots(slug, doctorId, date, durationMinutes),
    enabled: Boolean(doctorId && date && (services.length === 0 || serviceId)),
  });

  const canSubmit = useMemo(() => {
    if (!slot || !fullName.trim() || !contact.trim()) return false;
    if (services.length > 0 && !serviceId) return false;
    if (intake.email && !email.trim()) return false;
    if (intake.birthdate && !birthdate) return false;
    if (intake.sex && !sex) return false;
    if (intake.address && !address.trim()) return false;
    if (intake.reason && !reason.trim()) return false;
    if (intake.existing_patient && !existing) return false;
    return true;
  }, [
    slot,
    fullName,
    contact,
    services.length,
    serviceId,
    intake,
    email,
    birthdate,
    sex,
    address,
    reason,
    existing,
  ]);

  const book = useMutation({
    mutationFn: () =>
      api.requestPublicAppointment(slug, {
        doctor_id: doctorId,
        service_fee_id: serviceId || undefined,
        full_name: fullName.trim(),
        contact_number: contact.trim(),
        email: intake.email ? email.trim() : undefined,
        birthdate: intake.birthdate ? birthdate : undefined,
        sex: intake.sex ? sex : undefined,
        address: intake.address ? address.trim() : undefined,
        reason_for_visit: intake.reason ? reason.trim() : undefined,
        notes: intake.notes ? notes.trim() || undefined : undefined,
        is_existing_patient: intake.existing_patient
          ? existing === "existing"
          : undefined,
        scheduled_start: slot!.scheduled_start,
        scheduled_end: slot!.scheduled_end,
      }),
    onSuccess: (appt) => {
      setConfirmed(appt.appointment_status === "Confirmed");
      setDone(true);
      setError(null);
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) {
        setError("That slot was just taken. Pick another.");
        setSlot(null);
      } else {
        setError(err instanceof Error ? err.message : "Booking failed");
      }
    },
  });

  if (isLoading || !clinic) {
    return (
      <AuthLayout title="Book an appointment">
        <PublicBookingSkeleton />
      </AuthLayout>
    );
  }

  if (done && slot) {
    return (
      <AuthLayout title={clinic.name}>
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-success/10 text-success">
            <CalendarCheck className="size-6" />
          </span>
          <p className="text-sm text-muted-foreground">
            {confirmed
              ? `Your request at ${clinic.name} is confirmed.`
              : `Your request at ${clinic.name} was received.`}
          </p>
          <p className="text-sm font-medium text-foreground">
            {formatSlot(slot.scheduled_start)}
          </p>
          {selectedService ? (
            <p className="text-sm text-muted-foreground">
              {selectedService.name}
            </p>
          ) : null}
          {clinic.cancellation_notice_hours > 0 ? (
            <p className="text-sm text-muted-foreground">
              Cancel at least {clinic.cancellation_notice_hours} hours ahead.
            </p>
          ) : null}
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title={clinic.name}>
      {clinic.address && (
        <p className="-mt-4 mb-4 text-sm text-muted-foreground">
          {clinic.address}
        </p>
      )}
      <div className="flex flex-col gap-4">
        {clinic.doctors.length > 1 ? (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="doctor">Doctor</Label>
            <Select
              value={doctorId}
              onValueChange={(v) => {
                setDoctorId(v);
                setSlot(null);
              }}
            >
              <SelectTrigger id="doctor" className="min-h-11 w-full">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                {clinic.doctors.map((d) => (
                  <SelectItem key={d.id} value={d.id}>
                    {d.full_name}
                    {d.specialty ? ` · ${d.specialty}` : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : null}
        {services.length > 0 ? (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="service">Type</Label>
            <Select
              value={serviceId}
              onValueChange={(v) => {
                setServiceId(v);
                setSlot(null);
              }}
            >
              <SelectTrigger id="service" className="min-h-11 w-full">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                {services.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : null}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="date">Date</Label>
          <DatePicker
            id="date"
            min={today}
            max={maxDate}
            value={date}
            onValueChange={(next) => {
              setDate(next);
              setSlot(null);
            }}
          />
        </div>
        {doctorId && date && (services.length === 0 || serviceId) ? (
          <div className="text-sm">
            <p className="mb-2 font-medium text-foreground">Available times</p>
            {isFetching ? (
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-11 w-20 rounded-lg" />
                ))}
              </div>
            ) : (slots?.slots ?? []).length === 0 ? (
              <SectionCard>
                <EmptyState icon={CalendarCheck} heading="No slots" size="sm" />
              </SectionCard>
            ) : (
              <div className="flex flex-wrap gap-2">
                {slots?.slots.map((s) => {
                  const label = new Date(s.scheduled_start).toLocaleTimeString(
                    "en-PH",
                    {
                      timeZone: "Asia/Manila",
                      hour: "2-digit",
                      minute: "2-digit",
                    },
                  );
                  const selected = slot?.scheduled_start === s.scheduled_start;
                  return (
                    <Button
                      key={s.scheduled_start}
                      type="button"
                      size="sm"
                      variant={selected ? "default" : "outline"}
                      className="min-h-11 rounded-full px-4"
                      onClick={() => setSlot(s)}
                    >
                      {label}
                    </Button>
                  );
                })}
              </div>
            )}
          </div>
        ) : null}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="full-name">Full name</Label>
          <Input
            id="full-name"
            className="min-h-11"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder={FORM_PLACEHOLDERS.fullName}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="contact">Contact number</Label>
          <Input
            id="contact"
            className="min-h-11"
            inputMode="tel"
            value={contact}
            placeholder={FORM_PLACEHOLDERS.phone}
            onChange={(e) => setContact(e.target.value)}
          />
        </div>
        {intake.email ? (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              className="min-h-11"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={FORM_PLACEHOLDERS.email}
            />
          </div>
        ) : null}
        {intake.birthdate ? (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="birthdate">Birthdate</Label>
            <DatePicker
              id="birthdate"
              max={today}
              value={birthdate}
              onValueChange={setBirthdate}
            />
          </div>
        ) : null}
        {intake.sex ? (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="sex">Sex</Label>
            <Select value={sex} onValueChange={setSex}>
              <SelectTrigger id="sex" className="min-h-11 w-full">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Female">Female</SelectItem>
                <SelectItem value="Male">Male</SelectItem>
                <SelectItem value="Other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
        ) : null}
        {intake.address ? (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="address">Address</Label>
            <Input
              id="address"
              className="min-h-11"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder={FORM_PLACEHOLDERS.address}
            />
          </div>
        ) : null}
        {intake.reason ? (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reason">Reason</Label>
            <Input
              id="reason"
              className="min-h-11"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </div>
        ) : null}
        {intake.existing_patient ? (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="existing">New or existing</Label>
            <Select value={existing} onValueChange={setExisting}>
              <SelectTrigger id="existing" className="min-h-11 w-full">
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="new">New</SelectItem>
                <SelectItem value="existing">Existing</SelectItem>
              </SelectContent>
            </Select>
          </div>
        ) : null}
        {intake.notes ? (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        ) : null}
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button
          type="button"
          size="lg"
          className="min-h-11"
          disabled={!canSubmit || book.isPending}
          onClick={() => book.mutate()}
        >
          {book.isPending ? "Booking…" : "Confirm booking"}
        </Button>
      </div>
    </AuthLayout>
  );
}
