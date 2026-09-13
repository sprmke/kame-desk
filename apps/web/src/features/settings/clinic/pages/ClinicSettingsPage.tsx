import { useEffect, useState } from "react";
import { DoorOpen, Plus } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { DAYS, defaultHours } from "@/features/onboarding/lib/schemas";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { PageHeader } from "@/components/layout/PageHeader";
import { ClinicSettingsSkeleton } from "@/components/skeletons/PageSkeletons";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { TimePicker } from "@/components/ui/time-picker";
import { DatePicker } from "@/components/ui/date-picker";
import { ImageFileDropzone } from "@/components/ui/file-dropzone";
import {
  BrandColorField,
  DEFAULT_CLINIC_BRAND_COLOR,
} from "@/components/ui/brand-color-field";
import { NumberSlider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { BirCompliance, BirComplianceMode } from "@/lib/apiClient";
import { openBirCompliancePreviewPdf } from "@/features/billing/lib/receiptPdf";
import { RoomCreateModal } from "@/features/settings/clinic/components/RoomCreateModal";

const DAY_LABELS: Record<string, string> = {
  mon: "Monday",
  tue: "Tuesday",
  wed: "Wednesday",
  thu: "Thursday",
  fri: "Friday",
  sat: "Saturday",
  sun: "Sunday",
};

type Hours = Record<string, { open: string; close: string; closed: boolean }>;

export type ClinicSettingsView =
  "details" | "hours" | "rooms" | "branding" | "compliance";

const VIEW_TITLE: Record<ClinicSettingsView, string> = {
  details: "Clinic details",
  hours: "Hours and holidays",
  rooms: "Rooms",
  branding: "Branding",
  compliance: "Compliance",
};

export function ClinicSettingsPage({
  view = "details",
}: {
  view?: ClinicSettingsView;
}) {
  const clinicId = getClinicId()!;
  const qc = useQueryClient();
  const { data: clinic, isLoading } = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => api.getClinic(clinicId),
  });

  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [license, setLicense] = useState("");
  const [accreditation, setAccreditation] = useState("");
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [brandColor, setBrandColor] = useState(DEFAULT_CLINIC_BRAND_COLOR);
  const [soap, setSoap] = useState(false);
  const [hours, setHours] = useState<Hours>(defaultHours());
  const [holidays, setHolidays] = useState("");
  const [prefix, setPrefix] = useState("OR-");
  const [nextNumber, setNextNumber] = useState(1);
  const [padWidth, setPadWidth] = useState(6);

  useEffect(() => {
    if (!clinic) return;
    setName(clinic.name);
    setAddress(clinic.address ?? "");
    setPhone(clinic.contact_phone ?? "");
    setEmail(clinic.contact_email ?? "");
    setLicense(clinic.license_info ?? "");
    setAccreditation(clinic.accreditation_info ?? "");
    setLogoPreview(clinic.logo_url ?? null);
    setBrandColor(clinic.brand_color ?? DEFAULT_CLINIC_BRAND_COLOR);
    setSoap(clinic.reception_can_view_soap ?? false);
    setHours(clinic.working_hours ?? defaultHours());
    setHolidays((clinic.holiday_dates ?? []).join("\n"));
    if (clinic.receipt_numbering) {
      setPrefix(clinic.receipt_numbering.prefix);
      setNextNumber(clinic.receipt_numbering.next_number);
      setPadWidth(clinic.receipt_numbering.pad_width);
    }
  }, [clinic]);

  useEffect(() => {
    return () => {
      if (logoPreview?.startsWith("blob:")) URL.revokeObjectURL(logoPreview);
    };
  }, [logoPreview]);

  async function uploadLogo(file: File | undefined) {
    if (!file) return;
    if (logoPreview?.startsWith("blob:")) URL.revokeObjectURL(logoPreview);
    const preview = URL.createObjectURL(file);
    setLogoPreview(preview);
    setUploadingLogo(true);
    try {
      const { upload_url } = await api.clinicLogoUpload(clinicId, {
        content_type: file.type,
        file_size_bytes: file.size,
      });
      await fetch(upload_url, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });
      await qc.invalidateQueries({ queryKey: ["clinic", clinicId] });
    } catch {
      URL.revokeObjectURL(preview);
      setLogoPreview(clinic?.logo_url ?? null);
    } finally {
      setUploadingLogo(false);
    }
  }

  const saveProfile = useMutation({
    mutationFn: async () => {
      await api.patchClinic(clinicId, {
        name,
        address,
        contact_phone: phone,
        contact_email: email || null,
        license_info: license,
        accreditation_info: accreditation,
        brand_color: brandColor,
        reception_can_view_soap: soap,
      });
      await api.putWorkingHours(clinicId, {
        working_hours: hours,
        holiday_dates: holidays
          .split("\n")
          .map((d) => d.trim())
          .filter(Boolean),
      });
      await api.putReceiptNumbering(clinicId, {
        prefix,
        next_number: nextNumber,
        pad_width: padWidth,
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clinic", clinicId] }),
  });

  if (isLoading) {
    return (
      <div className="w-full">
        <PageHeader title={VIEW_TITLE[view]} />
        <ClinicSettingsSkeleton />
      </div>
    );
  }

  const showDetails = view === "details";
  const showBranding = view === "branding";
  const showHours = view === "hours";
  const showCompliance = view === "compliance";
  const showRooms = view === "rooms";

  return (
    <div className="w-full">
      <PageHeader title={VIEW_TITLE[view]} />
      <form
        className="flex flex-col gap-6"
        onSubmit={(e) => {
          e.preventDefault();
          saveProfile.mutate();
        }}
      >
        {showDetails || showBranding ? (
          <SettingsSection title={showBranding ? "Branding" : "Profile"}>
            {showDetails ? (
              <>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="clinic-name">Name</Label>
                  <Input
                    id="clinic-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={FORM_PLACEHOLDERS.clinicName}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="clinic-address">Address</Label>
                  <Input
                    id="clinic-address"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder={FORM_PLACEHOLDERS.address}
                  />
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="clinic-phone">Phone</Label>
                    <Input
                      id="clinic-phone"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder={FORM_PLACEHOLDERS.phone}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="clinic-email">Email</Label>
                    <Input
                      id="clinic-email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder={FORM_PLACEHOLDERS.email}
                    />
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="clinic-license">License</Label>
                  <Input
                    id="clinic-license"
                    value={license}
                    onChange={(e) => setLicense(e.target.value)}
                    placeholder={FORM_PLACEHOLDERS.license}
                  />
                </div>
                <div className="flex items-center justify-between gap-3">
                  <Label htmlFor="soap-toggle" className="font-normal">
                    Reception can view SOAP
                  </Label>
                  <Switch
                    id="soap-toggle"
                    checked={soap}
                    onCheckedChange={setSoap}
                  />
                </div>
              </>
            ) : null}
            {showBranding ? (
              <>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="clinic-logo">Logo</Label>
                  <ImageFileDropzone
                    id="clinic-logo"
                    accept="image/png,image/jpeg,image/webp"
                    imageUrl={logoPreview}
                    uploading={uploadingLogo}
                    emptyLabel="Upload logo"
                    onFileSelect={(file) => void uploadLogo(file)}
                    onRemove={() => {
                      if (logoPreview?.startsWith("blob:")) {
                        URL.revokeObjectURL(logoPreview);
                      }
                      setLogoPreview(null);
                    }}
                  />
                </div>
                <BrandColorField
                  id="clinic-brand-color"
                  value={brandColor}
                  onChange={setBrandColor}
                />
              </>
            ) : null}
          </SettingsSection>
        ) : null}

        {showHours ? (
          <SettingsSection title="Hours">
            <div className="flex flex-col divide-y divide-border rounded-lg border border-border">
              {DAYS.map((day) => (
                <div
                  key={day}
                  className="flex flex-wrap items-center gap-3 px-3 py-2.5"
                >
                  <span className="w-24 shrink-0 text-sm font-medium">
                    {DAY_LABELS[day]}
                  </span>
                  <TimePicker
                    className="h-9 w-32"
                    aria-label={`${DAY_LABELS[day]} open`}
                    value={hours[day]?.open ?? "09:00"}
                    disabled={hours[day]?.closed}
                    onValueChange={(open) =>
                      setHours({
                        ...hours,
                        [day]: {
                          ...hours[day],
                          open,
                          close: hours[day]?.close ?? "17:00",
                          closed: hours[day]?.closed ?? false,
                        },
                      })
                    }
                  />
                  <TimePicker
                    className="h-9 w-32"
                    aria-label={`${DAY_LABELS[day]} close`}
                    value={hours[day]?.close ?? "17:00"}
                    disabled={hours[day]?.closed}
                    onValueChange={(close) =>
                      setHours({
                        ...hours,
                        [day]: {
                          ...hours[day],
                          close,
                          open: hours[day]?.open ?? "09:00",
                          closed: hours[day]?.closed ?? false,
                        },
                      })
                    }
                  />
                  <Label className="ml-auto flex cursor-pointer items-center gap-2 text-xs text-muted-foreground">
                    Closed
                    <Switch
                      checked={hours[day]?.closed ?? false}
                      onCheckedChange={(closed) =>
                        setHours({
                          ...hours,
                          [day]: {
                            open: hours[day]?.open ?? "09:00",
                            close: hours[day]?.close ?? "17:00",
                            closed,
                          },
                        })
                      }
                    />
                  </Label>
                </div>
              ))}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="holidays">Holidays (YYYY-MM-DD)</Label>
              <Textarea
                id="holidays"
                rows={3}
                value={holidays}
                onChange={(e) => setHolidays(e.target.value)}
              />
            </div>
          </SettingsSection>
        ) : null}

        {showCompliance ? (
          <SettingsSection title="Receipt numbering">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="or-prefix">Prefix</Label>
              <Input
                id="or-prefix"
                value={prefix}
                onChange={(e) => setPrefix(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="or-next">Next number</Label>
              <Input
                id="or-next"
                type="number"
                min={1}
                value={nextNumber}
                onChange={(e) => setNextNumber(Number(e.target.value))}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <NumberSlider
                id="or-pad"
                label="Pad width"
                min={1}
                max={10}
                step={1}
                value={padWidth}
                onChange={setPadWidth}
              />
            </div>
          </SettingsSection>
        ) : null}

        {showDetails || showBranding || showHours || showCompliance ? (
          <Button
            type="submit"
            className="w-fit"
            disabled={saveProfile.isPending}
          >
            {saveProfile.isPending ? "Saving…" : "Save"}
          </Button>
        ) : null}
      </form>
      {showRooms ? (
        <div className="mt-6">
          <RoomsCard clinicId={clinicId} />
        </div>
      ) : null}
      {showCompliance ? (
        <div className="mt-6 flex flex-col gap-6">
          <BirComplianceCard clinicId={clinicId} />
          <GrowthSettingsCard clinicId={clinicId} />
        </div>
      ) : null}
    </div>
  );
}

const COMPLIANCE_MODE_LABEL: Record<BirComplianceMode, string> = {
  not_yet_accredited: "Not yet accredited",
  ptu: "Permit to Use (PTU)",
  cas: "Computerized Accounting System (CAS)",
};

function BirComplianceCard({ clinicId }: { clinicId: string }) {
  const qc = useQueryClient();
  const { data: bir } = useQuery({
    queryKey: ["bir-compliance", clinicId],
    queryFn: () => api.getBirCompliance(clinicId),
  });

  const [tin, setTin] = useState("");
  const [registeredName, setRegisteredName] = useState("");
  const [registeredAddress, setRegisteredAddress] = useState("");
  const [vatRegistered, setVatRegistered] = useState(false);
  const [mode, setMode] = useState<BirComplianceMode>("not_yet_accredited");
  const [accreditationNumber, setAccreditationNumber] = useState("");
  const [validUntil, setValidUntil] = useState("");

  useEffect(() => {
    if (!bir) return;
    setTin(bir.tin ?? "");
    setRegisteredName(bir.registered_name ?? "");
    setRegisteredAddress(bir.registered_address ?? "");
    setVatRegistered(bir.vat_registered);
    setMode(bir.compliance_mode);
    setAccreditationNumber(bir.accreditation_number ?? "");
    setValidUntil(bir.accreditation_valid_until ?? "");
  }, [bir]);

  function currentValues(): BirCompliance {
    return {
      tin: tin.trim() || null,
      registered_name: registeredName.trim() || null,
      registered_address: registeredAddress.trim() || null,
      vat_registered: vatRegistered,
      compliance_mode: mode,
      accreditation_number: accreditationNumber.trim() || null,
      accreditation_valid_until: validUntil || null,
    };
  }

  const save = useMutation({
    mutationFn: () => api.putBirCompliance(clinicId, currentValues()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bir-compliance", clinicId] });
      qc.invalidateQueries({ queryKey: ["clinic", clinicId] });
    },
  });

  const preview = useMutation({
    mutationFn: () => openBirCompliancePreviewPdf(clinicId, currentValues()),
  });

  const expired =
    Boolean(validUntil) && validUntil < new Date().toISOString().slice(0, 10);

  return (
    <SettingsSection title="BIR compliance">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <div className="flex flex-col gap-3 py-3">
          <p className="text-sm text-muted-foreground">
            These fields print on every receipt/invoice so it satisfies your
            clinic&apos;s own BIR filing — accreditation stays your
            responsibility.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="bir-tin">TIN</Label>
              <Input
                id="bir-tin"
                value={tin}
                onChange={(e) => setTin(e.target.value)}
                placeholder="000-000-000-000"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="bir-mode">Compliance mode</Label>
              <Select
                value={mode}
                onValueChange={(v) => setMode(v as BirComplianceMode)}
              >
                <SelectTrigger id="bir-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(COMPLIANCE_MODE_LABEL).map(
                    ([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ),
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="bir-name">Registered business name</Label>
            <Input
              id="bir-name"
              value={registeredName}
              onChange={(e) => setRegisteredName(e.target.value)}
              placeholder={"Defaults to clinic name if left blank"}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="bir-address">Registered address</Label>
            <Input
              id="bir-address"
              value={registeredAddress}
              onChange={(e) => setRegisteredAddress(e.target.value)}
              placeholder="Defaults to clinic address if left blank"
            />
          </div>
          {mode !== "not_yet_accredited" && (
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="bir-accreditation-number">
                  {mode === "ptu"
                    ? "Permit to Use No."
                    : "CAS Accreditation No."}
                </Label>
                <Input
                  id="bir-accreditation-number"
                  value={accreditationNumber}
                  onChange={(e) => setAccreditationNumber(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="bir-valid-until">Valid until</Label>
                <DatePicker
                  id="bir-valid-until"
                  value={validUntil}
                  onValueChange={setValidUntil}
                />
                {expired && (
                  <p className="text-sm text-warning">
                    This accreditation has expired.
                  </p>
                )}
              </div>
            </div>
          )}
          <div className="flex items-center justify-between gap-3">
            <Label htmlFor="bir-vat" className="font-normal">
              VAT registered
            </Label>
            <Switch
              id="bir-vat"
              checked={vatRegistered}
              onCheckedChange={setVatRegistered}
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 py-3">
          <Button
            type="button"
            variant="outline"
            disabled={preview.isPending}
            onClick={() => preview.mutate()}
          >
            {preview.isPending ? "Preparing…" : "Preview receipt"}
          </Button>
          <Button type="submit" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </SettingsSection>
  );
}

function GrowthSettingsCard({ clinicId }: { clinicId: string }) {
  const qc = useQueryClient();
  const { data: growth } = useQuery({
    queryKey: ["growth-settings", clinicId],
    queryFn: () => api.getGrowthSettings(clinicId),
  });

  const [reviewLink, setReviewLink] = useState("");
  const [reviewEnabled, setReviewEnabled] = useState(false);
  const [dohNumber, setDohNumber] = useState("");
  const [dohValidUntil, setDohValidUntil] = useState("");

  useEffect(() => {
    if (!growth) return;
    setReviewLink(growth.google_review_link ?? "");
    setReviewEnabled(growth.review_requests_enabled);
    setDohNumber(growth.doh_accreditation_number ?? "");
    setDohValidUntil(growth.doh_accreditation_valid_until ?? "");
  }, [growth]);

  const save = useMutation({
    mutationFn: () =>
      api.putGrowthSettings(clinicId, {
        google_review_link: reviewLink.trim() || null,
        review_requests_enabled: reviewEnabled,
        doh_accreditation_number: dohNumber.trim() || null,
        doh_accreditation_valid_until: dohValidUntil || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["growth-settings", clinicId] });
      qc.invalidateQueries({ queryKey: ["clinic", clinicId] });
    },
  });

  return (
    <SettingsSection title="Growth and retention">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <div className="flex flex-col gap-4 py-3">
          <div className="flex items-center justify-between gap-3 rounded-lg border border-border p-3">
            <div>
              <p className="text-sm font-medium text-foreground">
                Post-visit review & feedback requests
              </p>
              <p className="text-sm text-muted-foreground">
                Send a review request and a quick satisfaction survey after each
                completed visit.
              </p>
            </div>
            <Switch
              checked={reviewEnabled}
              onCheckedChange={setReviewEnabled}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="google-review-link">
              Google Business review link
            </Label>
            <Input
              id="google-review-link"
              value={reviewLink}
              onChange={(e) => setReviewLink(e.target.value)}
              placeholder="https://g.page/r/your-clinic/review"
            />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="doh-number">DOH accreditation number</Label>
              <Input
                id="doh-number"
                value={dohNumber}
                onChange={(e) => setDohNumber(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="doh-valid-until">Valid until</Label>
              <DatePicker
                id="doh-valid-until"
                value={dohValidUntil}
                onValueChange={setDohValidUntil}
              />
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            DOH accreditation is display-only, a trust signal for patients — it
            doesn&apos;t connect to a live DOH system.
          </p>
        </div>
        <div className="flex justify-end py-3">
          <Button type="submit" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </SettingsSection>
  );
}

function RoomsCard({ clinicId }: { clinicId: string }) {
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const { data: rooms } = useQuery({
    queryKey: ["rooms", clinicId],
    queryFn: () => api.listRooms(clinicId),
  });
  const toggle = useMutation({
    mutationFn: (room: { id: string; is_active: boolean }) =>
      api.patchRoom(clinicId, room.id, { is_active: !room.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rooms", clinicId] }),
  });

  return (
    <SettingsSection
      title="Rooms"
      divided={false}
      action={
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setCreateOpen(true)}
        >
          <Plus className="size-4" />
          New room
        </Button>
      }
    >
      <SectionCard>
        {(rooms ?? []).length === 0 ? (
          <EmptyState
            icon={DoorOpen}
            heading="No rooms yet"
            size="sm"
            action={
              <Button type="button" onClick={() => setCreateOpen(true)}>
                New room
              </Button>
            }
          />
        ) : (
          <ul className="flex flex-col gap-1 text-sm">
            {(rooms ?? []).map((r) => (
              <li
                key={r.id}
                className="flex items-center justify-between gap-2"
              >
                <span className={r.is_active ? "" : "text-muted-foreground"}>
                  {r.name}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => toggle.mutate(r)}
                >
                  {r.is_active ? "Hide" : "Show"}
                </Button>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>

      <RoomCreateModal
        clinicId={clinicId}
        open={createOpen}
        onOpenChange={setCreateOpen}
      />
    </SettingsSection>
  );
}
