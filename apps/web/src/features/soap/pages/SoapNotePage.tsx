import { Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { ChevronLeft, Download } from "lucide-react";
import { AssistantMark } from "@/components/brand/AssistantMark";
import { API_BASE } from "@/lib/apiBase";
import { api, type SoapNote } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import { getAccessToken, getClinicId } from "@/lib/auth";
import { useOnlineStatus } from "@/lib/onlineStatus";
import {
  enqueueSoapDraft,
  generateClientDraftToken,
} from "@/lib/offlineSoapQueue";
import { ActivityTrail } from "@/features/audit-log/components/ActivityTrail";
import { SpecialtyFields } from "@/features/soap/components/SpecialtyFields";
import { SoapRecordingPanel } from "@/features/soap/components/SoapRecordingPanel";
import { useSoapDraftStream } from "@/features/soap/hooks/useSoapDraftStream";
import { filterIcd10, type SoapFormValues } from "@/features/soap/lib/schemas";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { SoapNoteSkeleton } from "@/components/skeletons/PageSkeletons";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DatePicker } from "@/components/ui/date-picker";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type Props = { appointmentId: string };

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString("en-PH", {
    timeZone: "Asia/Manila",
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function SoapNotePage({ appointmentId }: Props) {
  const qc = useQueryClient();
  const [viewVersion, setViewVersion] = useState<number | null>(null);
  const [compareVersion, setCompareVersion] = useState<number | null>(null);
  const [icdQuery, setIcdQuery] = useState("");
  const [draftInput, setDraftInput] = useState("");
  const [aiDraftActive, setAiDraftActive] = useState(false);
  const [queuedOffline, setQueuedOffline] = useState(false);
  const online = useOnlineStatus();
  useEffect(() => {
    if (online) setQueuedOffline(false);
  }, [online]);
  const {
    start: startDraft,
    cancel: cancelDraft,
    isStreaming,
    error: draftError,
  } = useSoapDraftStream(appointmentId);

  const { data: appointment, isLoading: loadingAppointment } = useQuery({
    queryKey: ["appointment", appointmentId],
    queryFn: async () => {
      const list = await api.listAppointments();
      return list.items.find((a) => a.id === appointmentId) ?? null;
    },
  });

  const { data: templates } = useQuery({
    queryKey: ["specialty-templates"],
    queryFn: () => api.listSpecialtyTemplates(),
  });

  const { data: soapHistory, isLoading: loadingSoap } = useQuery({
    queryKey: ["soap-notes", appointmentId],
    queryFn: () => api.listSoapNotes(appointmentId),
  });

  const { data: vitals } = useQuery({
    queryKey: ["vitals", appointment?.patient_id],
    queryFn: () => api.listVitals(appointment!.patient_id),
    enabled: Boolean(appointment?.patient_id),
  });

  const latestVitals = vitals?.[0];

  const viewingNote: SoapNote | undefined = useMemo(() => {
    if (!soapHistory?.items.length) return undefined;
    if (viewVersion === null) return soapHistory.items[0];
    return soapHistory.items.find((n) => n.version_number === viewVersion);
  }, [soapHistory, viewVersion]);

  const isReadOnly = Boolean(viewingNote && viewVersion !== null);

  const form = useForm<SoapFormValues>({
    values: viewingNote
      ? {
          subjective: viewingNote.subjective ?? "",
          objective: viewingNote.objective ?? "",
          assessment: viewingNote.assessment ?? "",
          plan: viewingNote.plan ?? "",
          diagnosis_primary: viewingNote.diagnosis_primary ?? "",
          icd10_codes: viewingNote.icd10_codes ?? [],
          follow_up_date: viewingNote.follow_up_date ?? "",
          specialty_template_key:
            viewingNote.specialty_template_key ?? "general",
          specialty_data: viewingNote.specialty_data ?? {},
        }
      : {
          subjective: "",
          objective: latestVitals
            ? `BP ${latestVitals.blood_pressure ?? "-"}, HR ${latestVitals.heart_rate ?? "-"}`
            : "",
          assessment: "",
          plan: "",
          diagnosis_primary: "",
          icd10_codes: [],
          follow_up_date: "",
          specialty_template_key: "general",
          specialty_data: {},
        },
  });

  const saveSoap = useMutation({
    // Default networkMode "online" would pause this mutation indefinitely
    // while offline instead of running mutationFn — we need it to always run
    // so our own online/offline branch below (queue vs. send) takes over.
    networkMode: "always",
    mutationFn: async (body: SoapFormValues) => {
      const payload = {
        ...body,
        follow_up_date: body.follow_up_date || null,
        specialty_data: body.specialty_data ?? null,
      };
      if (!navigator.onLine) {
        return { queued: true, note: await queueOffline(payload) };
      }
      try {
        return {
          queued: false,
          note: await api.createSoapNote(appointmentId, payload),
        };
      } catch (err) {
        if (err instanceof ApiError) throw err;
        return { queued: true, note: await queueOffline(payload) };
      }
    },
    onSuccess: ({ queued }) => {
      setQueuedOffline(queued);
      if (!queued) {
        qc.invalidateQueries({ queryKey: ["soap-notes", appointmentId] });
      }
      setViewVersion(null);
    },
  });

  async function queueOffline(payload: Record<string, unknown>) {
    const clientDraftToken = generateClientDraftToken();
    await enqueueSoapDraft({
      clientDraftToken,
      appointmentId,
      body: { ...payload, client_draft_token: clientDraftToken },
      queuedAt: new Date().toISOString(),
    });
    return null;
  }

  const signSoap = useMutation({
    mutationFn: (version: number) => api.signSoapNote(appointmentId, version),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["soap-notes", appointmentId] }),
  });

  const icdHits = filterIcd10(icdQuery);
  const templateKey = form.watch("specialty_template_key") ?? "general";
  const specialtyData =
    (form.watch("specialty_data") as Record<string, unknown>) ?? {};
  const icdCodes = form.watch("icd10_codes") ?? [];

  function applyDraftField(field: string, value: string) {
    const key = field as keyof SoapFormValues;
    if (key in form.getValues()) {
      form.setValue(key, value, { shouldDirty: true });
    }
  }

  function clearAiDraftIndicator() {
    setAiDraftActive(false);
  }

  async function handleGenerateDraft(inputOverride?: string) {
    const text = (inputOverride ?? draftInput).trim();
    if (!text || isReadOnly) return;
    if (inputOverride) setDraftInput(inputOverride);
    await startDraft(text, (field, value) => {
      applyDraftField(field, value);
      setAiDraftActive(true);
    });
  }

  async function downloadPdf(version: number) {
    const token = getAccessToken();
    const clinicId = getClinicId();
    const res = await fetch(
      `${API_BASE}/appointments/${appointmentId}/soap-notes/${version}/pdf`,
      {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(clinicId ? { "X-Clinic-Id": clinicId } : {}),
        },
      },
    );
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  }

  if (loadingAppointment || loadingSoap) {
    return (
      <div className={pageContainerClass("narrow")}>
        <Link
          to="/dashboard/appointments"
          className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="size-4" />
          Appointments
        </Link>
        <SoapNoteSkeleton />
      </div>
    );
  }

  return (
    <div className={pageContainerClass("narrow")}>
      <Link
        to="/dashboard/appointments"
        className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="size-4" />
        Appointments
      </Link>
      <PageHeader
        title="SOAP note"
        description={
          appointment
            ? `${appointment.patient_name} · ${appointment.doctor_name}`
            : undefined
        }
      />

      {soapHistory?.items.length ? (
        <section className="mb-6">
          <h2 className="mb-2 text-sm font-semibold text-foreground">
            Versions
          </h2>
          <div className="flex flex-col gap-2">
            {soapHistory.items.map((note) => (
              <div
                key={note.id}
                className="flex flex-wrap items-center gap-2 text-sm"
              >
                <button
                  type="button"
                  className="font-medium text-primary hover:underline"
                  onClick={() => setViewVersion(note.version_number)}
                >
                  v{note.version_number} · {formatWhen(note.created_at)}
                  {note.author_name ? ` · ${note.author_name}` : ""}
                </button>
                {note.signed_at && (
                  <span className="text-xs text-muted-foreground">Signed</span>
                )}
                {viewVersion !== null &&
                  note.version_number !== viewVersion && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setCompareVersion(note.version_number)}
                    >
                      Diff
                    </Button>
                  )}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => downloadPdf(note.version_number)}
                >
                  <Download className="size-3.5" />
                  PDF
                </Button>
              </div>
            ))}
            {viewVersion !== null && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-fit"
                onClick={() => setViewVersion(null)}
              >
                New version
              </Button>
            )}
          </div>
        </section>
      ) : null}

      {viewVersion !== null && compareVersion !== null && soapHistory && (
        <section className="mb-6">
          <h2 className="mb-2 text-sm font-semibold text-foreground">
            Diff v{compareVersion} → v{viewVersion}
          </h2>
          <div className="flex flex-col gap-2 text-sm">
            {(["subjective", "objective", "assessment", "plan"] as const).map(
              (field) => {
                const left = soapHistory.items.find(
                  (n) => n.version_number === compareVersion,
                )?.[field];
                const right = soapHistory.items.find(
                  (n) => n.version_number === viewVersion,
                )?.[field];
                if (left === right) return null;
                return (
                  <div key={field}>
                    <p className="font-medium capitalize">{field}</p>
                    <p className="text-muted-foreground">{left || "(empty)"}</p>
                    <p className="text-foreground">{right || "(empty)"}</p>
                  </div>
                );
              },
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="w-fit"
              onClick={() => setCompareVersion(null)}
            >
              Close
            </Button>
          </div>
        </section>
      )}

      <form
        className="flex flex-col gap-4"
        onSubmit={form.handleSubmit((values) => saveSoap.mutate(values))}
      >
        {!isReadOnly && (
          <SoapRecordingPanel
            appointmentId={appointmentId}
            disabled={isStreaming}
            onUseTranscript={(text) => {
              void handleGenerateDraft(text);
            }}
          />
        )}

        {!isReadOnly && (
          <section className="mb-4 rounded-lg border border-dashed border-border p-4">
            <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-foreground">
              <AssistantMark className="size-4 text-primary" />
              AI draft
            </h2>
            <div>
              <Textarea
                rows={2}
                value={draftInput}
                disabled={isStreaming}
                placeholder="Visit notes to draft from"
                onChange={(e) => setDraftInput(e.target.value)}
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  disabled={isStreaming || !draftInput.trim()}
                  onClick={() => handleGenerateDraft()}
                >
                  {isStreaming ? "Drafting…" : "Draft"}
                </Button>
                {isStreaming && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => cancelDraft()}
                  >
                    Stop
                  </Button>
                )}
              </div>
              {aiDraftActive && (
                <p className="mt-2 text-xs text-warning">
                  AI draft. Review before saving.
                </p>
              )}
              {draftError && (
                <p className="mt-2 text-sm text-destructive">{draftError}</p>
              )}
            </div>
          </section>
        )}

        <section className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="template">Template</Label>
            <Select
              disabled={isReadOnly}
              value={templateKey}
              onValueChange={(value) =>
                form.setValue("specialty_template_key", value)
              }
            >
              <SelectTrigger id="template" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(templates ?? []).map((t) => (
                  <SelectItem key={t.template_key} value={t.template_key}>
                    {t.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <SpecialtyFields
            templateKey={templateKey}
            value={specialtyData}
            disabled={isReadOnly}
            onChange={(next) => form.setValue("specialty_data", next)}
            patientId={appointment?.patient_id}
            appointmentId={appointmentId}
            soapNoteId={viewingNote?.id}
          />

          {(["subjective", "objective", "assessment", "plan"] as const).map(
            (field) => (
              <div key={field} className="flex flex-col gap-1.5">
                <Label htmlFor={field} className="capitalize">
                  {field}
                </Label>
                <Textarea
                  id={field}
                  rows={3}
                  disabled={isReadOnly}
                  placeholder={
                    field === "subjective"
                      ? FORM_PLACEHOLDERS.soapSubjective
                      : field === "objective"
                        ? FORM_PLACEHOLDERS.soapObjective
                        : field === "assessment"
                          ? FORM_PLACEHOLDERS.soapAssessment
                          : FORM_PLACEHOLDERS.soapPlan
                  }
                  {...form.register(field, {
                    onChange: () => clearAiDraftIndicator(),
                  })}
                />
              </div>
            ),
          )}

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="diagnosis_primary">Primary diagnosis</Label>
            <Input
              id="diagnosis_primary"
              disabled={isReadOnly}
              placeholder={FORM_PLACEHOLDERS.diagnosis}
              {...form.register("diagnosis_primary")}
            />
          </div>

          {!isReadOnly && (
            <div className="relative flex flex-col gap-1.5">
              <Label htmlFor="icd-search">ICD-10 search</Label>
              <Input
                id="icd-search"
                placeholder={FORM_PLACEHOLDERS.icdSearch}
                value={icdQuery}
                onChange={(e) => setIcdQuery(e.target.value)}
              />
              {icdHits.length > 0 && (
                <ul className="absolute top-full z-10 mt-1 w-full overflow-hidden rounded-lg border border-border bg-popover shadow-theme-md">
                  {icdHits.map((hit) => (
                    <li key={hit.code}>
                      <button
                        type="button"
                        className="block w-full px-3 py-2 text-left text-sm hover:bg-secondary"
                        onClick={() => {
                          const current = form.getValues("icd10_codes") ?? [];
                          if (!current.includes(hit.code)) {
                            form.setValue("icd10_codes", [
                              ...current,
                              hit.code,
                            ]);
                          }
                          setIcdQuery("");
                        }}
                      >
                        {hit.code} · {hit.label}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {icdCodes.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {icdCodes.map((code) => (
                <Badge key={code} variant="brand">
                  {code}
                </Badge>
              ))}
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="follow_up_date">Follow-up date</Label>
            <DatePicker
              id="follow_up_date"
              disabled={isReadOnly}
              {...form.register("follow_up_date")}
              value={form.watch("follow_up_date") ?? ""}
            />
          </div>
        </section>

        {!isReadOnly && (
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={saveSoap.isPending}>
                {saveSoap.isPending ? "Saving…" : "Save"}
              </Button>
              {soapHistory?.items[0] && !soapHistory.items[0].signed_at && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() =>
                    signSoap.mutate(soapHistory.items[0].version_number)
                  }
                >
                  Sign latest
                </Button>
              )}
            </div>
            {queuedOffline && (
              <p className="text-sm text-warning">
                Saved locally. Will sync when you are back online.
              </p>
            )}
          </div>
        )}
      </form>

      <div className="mt-4">
        <ActivityTrail
          targetType="appointment"
          targetId={appointmentId}
          title="Activity"
        />
      </div>
    </div>
  );
}
