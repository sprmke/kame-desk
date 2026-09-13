import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { CalendarCheck } from "lucide-react";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { PublicAssistantChat } from "@/features/booking/components/PublicAssistantChat";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { todayIsoManila } from "@/lib/isoDate";
import { PublicBookingSkeleton } from "@/components/skeletons/PageSkeletons";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type Props = { slug: string };

export function PublicBookingPage({ slug }: Props) {
  const [doctorId, setDoctorId] = useState("");
  const [date, setDate] = useState("");
  const [slot, setSlot] = useState<{
    scheduled_start: string;
    scheduled_end: string;
  } | null>(null);
  const [fullName, setFullName] = useState("");
  const [contact, setContact] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: clinic, isLoading } = useQuery({
    queryKey: ["public-clinic", slug],
    queryFn: () => api.getPublicClinic(slug),
  });

  const { data: slots, isFetching } = useQuery({
    queryKey: ["public-slots", slug, doctorId, date],
    queryFn: () => api.getPublicSlots(slug, doctorId, date),
    enabled: Boolean(doctorId && date),
  });

  const book = useMutation({
    mutationFn: () =>
      api.requestPublicAppointment(slug, {
        doctor_id: doctorId,
        full_name: fullName,
        contact_number: contact,
        scheduled_start: slot!.scheduled_start,
        scheduled_end: slot!.scheduled_end,
      }),
    onSuccess: () => {
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

  if (done) {
    return (
      <AuthLayout title={clinic.name}>
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-success/10 text-success">
            <CalendarCheck className="size-6" />
          </span>
          <p className="text-sm text-muted-foreground">
            Your request at {clinic.name} is confirmed. We will see you then.
          </p>
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
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="doctor">Doctor</Label>
          <Select
            value={doctorId}
            onValueChange={(v) => {
              setDoctorId(v);
              setSlot(null);
            }}
          >
            <SelectTrigger id="doctor">
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
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="date">Date</Label>
          <DatePicker
            id="date"
            min={todayIsoManila()}
            value={date}
            onValueChange={(next) => {
              setDate(next);
              setSlot(null);
            }}
          />
        </div>
        {doctorId && date && (
          <div className="text-sm">
            <p className="mb-2 font-medium text-foreground">Available times</p>
            {isFetching ? (
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-9 w-20 rounded-lg" />
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
                      className="rounded-full"
                      onClick={() => setSlot(s)}
                    >
                      {label}
                    </Button>
                  );
                })}
              </div>
            )}
          </div>
        )}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="full-name">Full name</Label>
          <Input
            id="full-name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder={FORM_PLACEHOLDERS.fullName}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="contact">Contact number</Label>
          <Input
            id="contact"
            inputMode="tel"
            value={contact}
            placeholder={FORM_PLACEHOLDERS.phone}
            onChange={(e) => setContact(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button
          type="button"
          size="lg"
          disabled={!slot || !fullName || !contact || book.isPending}
          onClick={() => book.mutate()}
        >
          {book.isPending ? "Booking…" : "Confirm booking"}
        </Button>
      </div>
      <PublicAssistantChat slug={slug} />
    </AuthLayout>
  );
}
