import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import {
  ChevronLeft,
  FileText,
  HeartPulse,
  History,
  Inbox,
  Pill,
  Receipt,
} from "lucide-react";
import { ActivityTrail } from "@/features/audit-log/components/ActivityTrail";
import { PatientEligibilityCard } from "@/features/billing/components/PatientEligibilityCard";
import { PatientMembershipCard } from "@/features/billing/components/PatientMembershipCard";
import { api } from "@/lib/apiClient";
import type { MedicalInfo } from "@/lib/apiClient";
import { useSession } from "@/hooks/useSession";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { InitialsAvatar } from "@/components/PersonIdentity";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { PatientDetailSkeleton } from "@/components/skeletons/PageSkeletons";
import { Input } from "@/components/ui/input";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { Field } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
import { PatientDetailSubNav } from "@/features/patients/components/PatientDetailSubNav";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type PatientDetailSection =
  | "overview"
  | "timeline"
  | "prescriptions"
  | "billing"
  | "orders"
  | "documents"
  | "activity";

type Props = {
  patientId: string;
  section?: PatientDetailSection;
};

export function PatientDetailPage({ patientId, section = "overview" }: Props) {
  const qc = useQueryClient();

  const { data: patient, isLoading } = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => api.getPatient(patientId),
  });

  const { data: medical } = useQuery({
    queryKey: ["medical-info", patientId],
    queryFn: () => api.getMedicalInfo(patientId),
    enabled: Boolean(patient),
  });

  const { data: vitals } = useQuery({
    queryKey: ["vitals", patientId],
    queryFn: () => api.listVitals(patientId),
    enabled: Boolean(patient),
  });

  const { data: files } = useQuery({
    queryKey: ["patient-files", patientId],
    queryFn: () => api.listPatientFiles(patientId),
    enabled: Boolean(patient),
  });

  const { data: prescriptions } = useQuery({
    queryKey: ["prescriptions", patientId],
    queryFn: () => api.listPrescriptions(patientId),
    enabled: Boolean(patient),
  });

  const { data: invoices } = useQuery({
    queryKey: ["invoices", patientId],
    queryFn: () => api.listInvoices(patientId),
    enabled: Boolean(patient),
  });

  const { data: balance } = useQuery({
    queryKey: ["patient-balance", patientId],
    queryFn: () => api.getPatientBalance(patientId),
    enabled: Boolean(patient),
  });

  const { data: documents } = useQuery({
    queryKey: ["patient-documents", patientId],
    queryFn: () => api.listPatientDocuments(patientId),
    enabled: Boolean(patient),
  });

  const { data: orders } = useQuery({
    queryKey: ["clinical-orders", patientId],
    queryFn: () => api.listClinicalOrders(patientId),
    enabled: Boolean(patient),
  });

  const { data: appointments } = useQuery({
    queryKey: ["appointments", { patient_id: patientId }],
    queryFn: () => api.listAppointments({ patient_id: patientId }),
    enabled: Boolean(patient),
  });

  const { can } = useSession();
  const canMerge = can("patients:merge");

  const medForm = useForm<MedicalInfo>({
    values: medical ?? {
      allergies_reviewed: false,
      allergies: [],
      medical_history: null,
      family_history: null,
      surgical_history: null,
      current_medications: [],
      chronic_conditions: [],
      vaccination_history: [],
      clinical_notes: null,
    },
  });

  const [allergy, setAllergy] = useState("");
  const [medication, setMedication] = useState("");
  const [condition, setCondition] = useState("");
  const [vaccine, setVaccine] = useState("");
  const [mergeSource, setMergeSource] = useState("");
  const [hmo, setHmo] = useState("");
  const [memberId, setMemberId] = useState("");
  const [contact, setContact] = useState("");
  const [remindersOptedOut, setRemindersOptedOut] = useState(false);

  const saveMedical = useMutation({
    mutationFn: (body: MedicalInfo) => api.putMedicalInfo(patientId, body),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["medical-info", patientId] }),
  });

  const saveDemo = useMutation({
    mutationFn: () =>
      api.patchPatient(patientId, {
        contact_number: contact || null,
        insurance_info: {
          provider: hmo || null,
          member_id: memberId || null,
        },
        reminders_opted_out: remindersOptedOut,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["patient", patientId] }),
  });

  const merge = useMutation({
    mutationFn: () => api.mergePatients(patientId, mergeSource),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["patient", patientId] });
      qc.invalidateQueries({ queryKey: ["appointments"] });
      setMergeSource("");
    },
  });

  const [orderName, setOrderName] = useState("");
  const [orderType, setOrderType] = useState<"lab" | "imaging">("lab");
  const createOrder = useMutation({
    mutationFn: () =>
      api.createClinicalOrder(patientId, {
        order_type: orderType,
        name: orderName.trim(),
      }),
    onSuccess: () => {
      setOrderName("");
      qc.invalidateQueries({ queryKey: ["clinical-orders", patientId] });
    },
  });
  const patchOrder = useMutation({
    mutationFn: (args: {
      orderId: string;
      status?: string;
      result_summary?: string;
    }) => api.patchClinicalOrder(patientId, args.orderId, args),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["clinical-orders", patientId] }),
  });
  const patchReferral = useMutation({
    mutationFn: (args: {
      documentId: string;
      referral_status?: string;
      referral_outcome?: string;
    }) => api.patchDocument(args.documentId, args),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["patient-documents", patientId] }),
  });
  const [chartShareByDoc, setChartShareByDoc] = useState<
    Record<string, string>
  >({});
  const [copiedDocId, setCopiedDocId] = useState<string | null>(null);
  const chartShare = useMutation({
    mutationFn: (documentId: string) => api.createChartShare(documentId),
    onSuccess: (data, documentId) => {
      setChartShareByDoc((prev) => ({ ...prev, [documentId]: data.share_url }));
    },
  });

  useEffect(() => {
    if (!patient) return;
    setContact(patient.contact_number ?? "");
    setRemindersOptedOut(Boolean(patient.reminders_opted_out));
    setHmo(patient.insurance_info?.provider ?? "");
    setMemberId(patient.insurance_info?.member_id ?? "");
  }, [patient]);

  if (isLoading || !patient) {
    return <PatientDetailSkeleton />;
  }

  const hasBalance = balance && Number(balance.outstanding_balance) > 0;
  const allergyNames = (medical?.allergies ?? [])
    .map((entry) => entry.substance)
    .filter(Boolean);
  const identityMeta = [
    `#${patient.patient_number}`,
    allergyNames.length
      ? `Allergies: ${allergyNames.join(", ")}`
      : "No allergies on file",
    hasBalance ? `Balance PHP ${balance.outstanding_balance}` : null,
  ]
    .filter(Boolean)
    .join(" · ");
  const timeline = [
    ...(appointments?.items ?? []).map((a) => ({
      id: `a-${a.id}`,
      at: a.scheduled_start,
      label: `Visit · ${a.appointment_status}`,
    })),
    ...(prescriptions?.items ?? []).map((rx) => ({
      id: `rx-${rx.id}`,
      at: rx.created_at,
      label: `Rx · ${rx.status}`,
    })),
    ...(invoices?.items ?? []).map((inv) => ({
      id: `inv-${inv.id}`,
      at: inv.created_at,
      label: `Invoice · ${inv.invoice_number ?? inv.status}`,
    })),
    ...(documents?.items ?? []).map((doc) => ({
      id: `doc-${doc.id}`,
      at: doc.created_at,
      label: `Document · ${doc.template_name ?? doc.document_type}`,
    })),
  ].sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());

  return (
    <div className={pageContainerClass()}>
      <Link
        to="/dashboard/patients"
        className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="size-4" />
        Patients
      </Link>

      <PageHeader
        title={patient.full_name}
        description={identityMeta}
        leading={
          <InitialsAvatar
            name={patient.full_name}
            seed={String(patient.patient_number)}
            className="size-10 text-sm"
          />
        }
        actions={
          <>
            <Button asChild variant="outline" size="sm">
              <Link
                to="/dashboard/patients/$patientId/documents/new"
                params={{ patientId }}
              >
                <FileText className="size-4" />
                Document
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link
                to="/dashboard/patients/$patientId/invoices/new"
                params={{ patientId }}
              >
                <Receipt className="size-4" />
                Invoice
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link
                to="/dashboard/patients/$patientId/prescriptions/new"
                params={{ patientId }}
              >
                <Pill className="size-4" />
                Rx
              </Link>
            </Button>
            <Button asChild size="sm">
              <Link to="/dashboard/appointments/new" search={{ patientId }}>
                Book
              </Link>
            </Button>
          </>
        }
        subNav={<PatientDetailSubNav patientId={patientId} />}
      />

      {section === "overview" ? (
        <div className="flex flex-col gap-4">
          <section className="mb-8">
            <h2 className="mb-2 text-sm font-semibold text-foreground">
              Demographics
            </h2>
            <div>
              <form
                className="grid gap-3 sm:grid-cols-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  saveDemo.mutate();
                }}
              >
                <Field>
                  <FieldLabel htmlFor="demo-contact" label="Contact" />
                  <Input
                    id="demo-contact"
                    value={contact}
                    onChange={(e) => setContact(e.target.value)}
                    placeholder={FORM_PLACEHOLDERS.phone}
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="demo-email" label="Email" />
                  <Input id="demo-email" value={patient.email ?? ""} disabled />
                </Field>
                <Field>
                  <FieldLabel htmlFor="demo-hmo" label="HMO" />
                  <Input
                    id="demo-hmo"
                    value={hmo}
                    onChange={(e) => setHmo(e.target.value)}
                    placeholder={FORM_PLACEHOLDERS.hmo}
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="demo-member" label="Member ID" />
                  <Input
                    id="demo-member"
                    value={memberId}
                    onChange={(e) => setMemberId(e.target.value)}
                    placeholder={FORM_PLACEHOLDERS.memberId}
                  />
                </Field>
                <label className="col-span-full flex items-center gap-2 text-sm">
                  <Checkbox
                    checked={remindersOptedOut}
                    onCheckedChange={(v) => setRemindersOptedOut(v === true)}
                  />
                  Opt out of reminders
                </label>
                <Button
                  type="submit"
                  variant="outline"
                  size="sm"
                  className="w-fit"
                  disabled={saveDemo.isPending}
                >
                  {saveDemo.isPending ? "Saving…" : "Save"}
                </Button>
              </form>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="mb-2 text-sm font-semibold text-foreground">
              Medical info
            </h2>
            <div>
              <form
                className="flex flex-col gap-3"
                onSubmit={medForm.handleSubmit((v) => saveMedical.mutate(v))}
              >
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <Checkbox
                    checked={medForm.watch("allergies_reviewed")}
                    onCheckedChange={(checked) =>
                      medForm.setValue("allergies_reviewed", checked === true)
                    }
                  />
                  Allergies reviewed
                </label>
                <div className="flex flex-col gap-1.5">
                  <FieldLabel label="Allergies" />
                  <div className="flex flex-wrap gap-1">
                    {medForm.watch("allergies").map((a, i) => (
                      <Button
                        key={`${a.substance}-${i}`}
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          medForm.setValue(
                            "allergies",
                            medForm
                              .getValues("allergies")
                              .filter((_, idx) => idx !== i),
                          )
                        }
                      >
                        {a.substance}
                      </Button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      value={allergy}
                      onChange={(e) => setAllergy(e.target.value)}
                      placeholder="Substance"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        if (!allergy.trim()) return;
                        medForm.setValue("allergies", [
                          ...medForm.getValues("allergies"),
                          { substance: allergy.trim() },
                        ]);
                        setAllergy("");
                      }}
                    >
                      Add
                    </Button>
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <FieldLabel label="Medications" />
                  <div className="flex flex-wrap gap-1">
                    {medForm.watch("current_medications").map((m, i) => (
                      <Button
                        key={`${m.name}-${i}`}
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          medForm.setValue(
                            "current_medications",
                            medForm
                              .getValues("current_medications")
                              .filter((_, idx) => idx !== i),
                          )
                        }
                      >
                        {m.name}
                      </Button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      value={medication}
                      onChange={(e) => setMedication(e.target.value)}
                      placeholder={FORM_PLACEHOLDERS.drugName}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        if (!medication.trim()) return;
                        medForm.setValue("current_medications", [
                          ...medForm.getValues("current_medications"),
                          { name: medication.trim() },
                        ]);
                        setMedication("");
                      }}
                    >
                      Add
                    </Button>
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <FieldLabel label="Conditions" />
                  <div className="flex flex-wrap gap-1">
                    {medForm.watch("chronic_conditions").map((c) => (
                      <Button
                        key={c}
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          medForm.setValue(
                            "chronic_conditions",
                            medForm
                              .getValues("chronic_conditions")
                              .filter((x) => x !== c),
                          )
                        }
                      >
                        {c}
                      </Button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      value={condition}
                      onChange={(e) => setCondition(e.target.value)}
                      placeholder={FORM_PLACEHOLDERS.condition}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        if (!condition.trim()) return;
                        medForm.setValue("chronic_conditions", [
                          ...medForm.getValues("chronic_conditions"),
                          condition.trim(),
                        ]);
                        setCondition("");
                      }}
                    >
                      Add
                    </Button>
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <FieldLabel label="Vaccines" />
                  <div className="flex flex-wrap gap-1">
                    {medForm.watch("vaccination_history").map((v) => (
                      <Button
                        key={v}
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          medForm.setValue(
                            "vaccination_history",
                            medForm
                              .getValues("vaccination_history")
                              .filter((x) => x !== v),
                          )
                        }
                      >
                        {v}
                      </Button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      value={vaccine}
                      onChange={(e) => setVaccine(e.target.value)}
                      placeholder={FORM_PLACEHOLDERS.vaccine}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        if (!vaccine.trim()) return;
                        medForm.setValue("vaccination_history", [
                          ...medForm.getValues("vaccination_history"),
                          vaccine.trim(),
                        ]);
                        setVaccine("");
                      }}
                    >
                      Add
                    </Button>
                  </div>
                </div>
                <Button
                  type="submit"
                  variant="outline"
                  size="sm"
                  className="w-fit"
                  disabled={saveMedical.isPending}
                >
                  {saveMedical.isPending ? "Saving…" : "Save medical info"}
                </Button>
              </form>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="mb-2 text-sm font-semibold text-foreground">
              Vitals
            </h2>
            <SectionCard>
              {(vitals ?? []).length === 0 ? (
                <EmptyState
                  icon={HeartPulse}
                  heading="No vitals recorded"
                  size="sm"
                />
              ) : (
                <ul className="flex flex-col divide-y divide-border text-sm">
                  {vitals?.map((v) => (
                    <li key={v.id} className="py-2 first:pt-0 last:pb-0">
                      {new Date(v.recorded_at).toLocaleString("en-PH", {
                        timeZone: "Asia/Manila",
                      })}
                      {v.blood_pressure ? ` · BP ${v.blood_pressure}` : ""}
                      {v.weight_kg ? ` · ${v.weight_kg} kg` : ""}
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>
          </section>

          <section className="mb-8">
            <h2 className="mb-2 text-sm font-semibold text-foreground">
              Files
            </h2>
            <SectionCard>
              {(files ?? []).length === 0 ? (
                <EmptyState icon={FileText} heading="No files yet" size="sm" />
              ) : (
                <ul className="flex flex-col divide-y divide-border text-sm">
                  {files?.map((f) => (
                    <li
                      key={f.id}
                      className="flex items-center justify-between py-2 first:pt-0 last:pb-0"
                    >
                      <span className="text-foreground">{f.file_type}</span>
                      {f.download_url && (
                        <a
                          className="font-medium text-primary hover:underline"
                          href={f.download_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>
          </section>

          {canMerge && (
            <section className="mb-8">
              <h2 className="mb-2 text-sm font-semibold text-foreground">
                Merge duplicate
              </h2>
              <div className="flex flex-col gap-3">
                <Field>
                  <FieldLabel
                    htmlFor="merge-source"
                    label="Source patient ID"
                  />
                  <Input
                    id="merge-source"
                    value={mergeSource}
                    onChange={(e) => setMergeSource(e.target.value)}
                    placeholder={FORM_PLACEHOLDERS.mergePatientId}
                  />
                </Field>
                {merge.isError && (
                  <p className="text-sm text-destructive">
                    {merge.error.message}
                  </p>
                )}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="w-fit"
                  disabled={!mergeSource || merge.isPending}
                  onClick={() => merge.mutate()}
                >
                  {merge.isPending ? "Merging…" : "Merge into this chart"}
                </Button>
              </div>
            </section>
          )}
        </div>
      ) : null}

      {section === "timeline" ? (
        <section className="mb-8">
          <h2 className="mb-2 text-sm font-semibold text-foreground">
            Timeline
          </h2>
          <SectionCard>
            {timeline.length === 0 ? (
              <EmptyState icon={History} heading="No events yet" size="sm" />
            ) : (
              <ul className="flex flex-col divide-y divide-border text-sm">
                {timeline.map((event) => (
                  <li
                    key={event.id}
                    className="flex flex-wrap justify-between gap-2 py-2 first:pt-0 last:pb-0"
                  >
                    <span className="text-foreground">{event.label}</span>
                    <span className="text-muted-foreground">
                      {new Date(event.at).toLocaleString("en-PH", {
                        timeZone: "Asia/Manila",
                      })}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </section>
      ) : null}

      {section === "prescriptions" ? (
        <section className="mb-8">
          <h2 className="mb-2 text-sm font-semibold text-foreground">
            Prescriptions
          </h2>
          <SectionCard>
            {(prescriptions?.items ?? []).length === 0 ? (
              <EmptyState
                icon={Pill}
                heading="No prescriptions yet"
                size="sm"
                action={
                  <Button asChild size="sm">
                    <Link
                      to="/dashboard/patients/$patientId/prescriptions/new"
                      params={{ patientId }}
                    >
                      New Rx
                    </Link>
                  </Button>
                }
              />
            ) : (
              <ul className="flex flex-col divide-y divide-border text-sm">
                {prescriptions?.items.map((rx) => (
                  <li
                    key={rx.id}
                    className="flex flex-wrap items-center justify-between gap-2 py-3 first:pt-0 last:pb-0"
                  >
                    <div>
                      <span className="font-medium text-foreground capitalize">
                        {rx.status}
                      </span>
                      {rx.doctor_name ? ` · ${rx.doctor_name}` : ""}
                      <div className="text-muted-foreground">
                        {rx.items.map((i) => i.drug_name).join(", ")}
                      </div>
                      {rx.override_reason && (
                        <div className="text-xs text-warning">
                          Override: {rx.override_reason}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-3">
                      {rx.pdf_download_url && (
                        <a
                          className="text-sm font-medium text-primary hover:underline"
                          href={rx.pdf_download_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          PDF
                        </a>
                      )}
                      <Link
                        to="/dashboard/patients/$patientId/prescriptions/new"
                        params={{ patientId }}
                        search={{
                          template: JSON.stringify(
                            rx.items.map((i) => ({
                              drug_name: i.drug_name,
                              dosage: i.dosage,
                              frequency: i.frequency,
                              duration: i.duration,
                              quantity: i.quantity,
                            })),
                          ),
                        }}
                        className="text-sm font-medium text-primary hover:underline"
                      >
                        Use as template
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </section>
      ) : null}

      {section === "billing" ? (
        <div className="flex flex-col gap-4">
          <PatientEligibilityCard patientId={patientId} />
          <PatientMembershipCard patientId={patientId} />
          <section className="mb-8">
            <h2 className="mb-2 text-sm font-semibold text-foreground">
              Invoices
            </h2>
            <SectionCard>
              {(invoices?.items ?? []).length === 0 ? (
                <EmptyState
                  icon={Receipt}
                  heading="No invoices yet"
                  size="sm"
                  action={
                    <Button asChild size="sm">
                      <Link
                        to="/dashboard/patients/$patientId/invoices/new"
                        params={{ patientId }}
                      >
                        New invoice
                      </Link>
                    </Button>
                  }
                />
              ) : (
                <ul className="flex flex-col divide-y divide-border text-sm">
                  {invoices?.items.map((inv) => (
                    <li
                      key={inv.id}
                      className="flex flex-wrap items-center justify-between gap-2 py-3 first:pt-0 last:pb-0"
                    >
                      <div>
                        <span className="font-medium text-foreground">
                          {inv.invoice_number ?? inv.status}
                        </span>
                        <div className="text-muted-foreground">
                          PHP {inv.total}
                          {Number(inv.balance_due) > 0
                            ? ` · due ${inv.balance_due}`
                            : ""}
                        </div>
                      </div>
                      <Link
                        to="/dashboard/patients/$patientId/invoices/$invoiceId"
                        params={{ patientId, invoiceId: inv.id }}
                        className="text-sm font-medium text-primary hover:underline"
                      >
                        View
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>
          </section>
        </div>
      ) : null}

      {section === "orders" ? (
        <section className="mb-8">
          <h2 className="mb-2 text-sm font-semibold text-foreground">
            Lab and imaging
          </h2>
          <div className="flex flex-col gap-4">
            <form
              className="flex flex-col gap-2 sm:flex-row sm:items-end"
              onSubmit={(e) => {
                e.preventDefault();
                if (!orderName.trim()) return;
                createOrder.mutate();
              }}
            >
              <Field className="min-w-0 flex-1">
                <FieldLabel htmlFor="order-name" label="Order" />
                <Input
                  id="order-name"
                  value={orderName}
                  onChange={(e) => setOrderName(e.target.value)}
                  placeholder={FORM_PLACEHOLDERS.orderName}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="order-type" label="Type" />
                <Select
                  value={orderType}
                  onValueChange={(v) => setOrderType(v as "lab" | "imaging")}
                >
                  <SelectTrigger id="order-type" className="w-full sm:w-36">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="lab">Lab</SelectItem>
                    <SelectItem value="imaging">Imaging</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Button
                type="submit"
                disabled={createOrder.isPending || !orderName.trim()}
              >
                Add
              </Button>
            </form>
            {(orders ?? []).length === 0 ? (
              <SectionCard>
                <EmptyState icon={Inbox} heading="No orders yet" size="sm" />
              </SectionCard>
            ) : (
              <SectionCard>
                <ul className="flex flex-col divide-y divide-border text-sm">
                  {orders?.map((order) => (
                    <li
                      key={order.id}
                      className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <span className="font-medium text-foreground">
                            {order.name}
                          </span>
                          <span className="text-muted-foreground">
                            {" "}
                            · {order.order_type}
                          </span>
                        </div>
                        <Select
                          value={order.status}
                          onValueChange={(status) =>
                            patchOrder.mutate({
                              orderId: order.id,
                              status,
                            })
                          }
                        >
                          <SelectTrigger
                            size="sm"
                            className="w-[140px]"
                            aria-label={`Status for ${order.name}`}
                          >
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="ordered">Ordered</SelectItem>
                            <SelectItem value="in_progress">
                              In progress
                            </SelectItem>
                            <SelectItem value="resulted">Resulted</SelectItem>
                            <SelectItem value="cancelled">Cancelled</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Input
                        defaultValue={order.result_summary ?? ""}
                        placeholder="Result"
                        aria-label={`Result for ${order.name}`}
                        onBlur={(e) => {
                          const value = e.target.value.trim();
                          if (value === (order.result_summary ?? "")) return;
                          patchOrder.mutate({
                            orderId: order.id,
                            result_summary: value,
                          });
                        }}
                      />
                    </li>
                  ))}
                </ul>
              </SectionCard>
            )}
          </div>
        </section>
      ) : null}

      {section === "documents" ? (
        <section className="mb-8">
          <h2 className="mb-2 text-sm font-semibold text-foreground">
            Documents
          </h2>
          <SectionCard>
            {(documents?.items ?? []).length === 0 ? (
              <EmptyState
                icon={FileText}
                heading="No documents yet"
                size="sm"
                action={
                  <Button asChild size="sm">
                    <Link
                      to="/dashboard/patients/$patientId/documents/new"
                      params={{ patientId }}
                    >
                      New document
                    </Link>
                  </Button>
                }
              />
            ) : (
              <ul className="flex flex-col divide-y divide-border text-sm">
                {documents?.items.map((doc) => (
                  <li
                    key={doc.id}
                    className="flex flex-col gap-2 py-2.5 first:pt-0 last:pb-0"
                  >
                    <div>
                      <span className="font-medium text-foreground">
                        {doc.template_name ?? doc.document_type}
                      </span>
                      <span className="text-muted-foreground">
                        {" "}
                        · {doc.status}
                      </span>
                    </div>
                    {doc.document_type === "referral_letter" && (
                      <div className="flex flex-col gap-2 sm:flex-row">
                        <Select
                          value={doc.referral_status ?? "draft"}
                          onValueChange={(referral_status) =>
                            patchReferral.mutate({
                              documentId: doc.id,
                              referral_status,
                            })
                          }
                        >
                          <SelectTrigger
                            size="sm"
                            className="w-[150px]"
                            aria-label="Referral status"
                          >
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="draft">Draft</SelectItem>
                            <SelectItem value="sent">Sent</SelectItem>
                            <SelectItem value="acknowledged">
                              Acknowledged
                            </SelectItem>
                            <SelectItem value="completed">Completed</SelectItem>
                          </SelectContent>
                        </Select>
                        <Input
                          defaultValue={doc.referral_outcome ?? ""}
                          placeholder="Outcome"
                          aria-label="Referral outcome"
                          onBlur={(e) => {
                            const value = e.target.value.trim();
                            if (value === (doc.referral_outcome ?? "")) return;
                            patchReferral.mutate({
                              documentId: doc.id,
                              referral_outcome: value,
                            });
                          }}
                        />
                        {doc.referral_recipient ? (
                          <p className="self-center text-muted-foreground">
                            To {doc.referral_recipient}
                          </p>
                        ) : null}
                      </div>
                    )}
                    {doc.document_type === "referral_letter" && (
                      <div className="flex flex-wrap items-center gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={chartShare.isPending}
                          onClick={() => chartShare.mutate(doc.id)}
                        >
                          Share chart summary
                        </Button>
                        {chartShareByDoc[doc.id] && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={async () => {
                              await navigator.clipboard.writeText(
                                chartShareByDoc[doc.id],
                              );
                              setCopiedDocId(doc.id);
                              setTimeout(() => setCopiedDocId(null), 2000);
                            }}
                          >
                            {copiedDocId === doc.id
                              ? "Copied"
                              : "Copy link (expires in 7 days)"}
                          </Button>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </section>
      ) : null}

      {section === "activity" ? (
        <ActivityTrail targetType="patient" targetId={patientId} />
      ) : null}
    </div>
  );
}
