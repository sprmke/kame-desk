import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { DAYS, defaultHours } from "@/features/onboarding/lib/schemas";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { PageHeader } from "@/components/layout/PageHeader";
import { ClinicSettingsSkeleton } from "@/components/skeletons/PageSkeletons";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { TimePicker } from "@/components/ui/time-picker";
import { ImageFileDropzone } from "@/components/ui/file-dropzone";
import {
  BrandColorField,
  DEFAULT_CLINIC_BRAND_COLOR,
} from "@/components/ui/brand-color-field";
import { NumberSlider } from "@/components/ui/slider";

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
  rooms: "Clinic details",
  branding: "Branding",
  compliance: "Receipts",
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
                    Secretary can view SOAP
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
    </div>
  );
}
