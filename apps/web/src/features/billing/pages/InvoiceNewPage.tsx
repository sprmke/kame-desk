import { Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ChevronLeft, Plus } from "lucide-react";
import { api, type InvoiceLineItemInput } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { useOnlineStatus } from "@/lib/onlineStatus";
import {
  confidenceClass,
  extractionToLineItem,
  type BillingExtractionDraft,
} from "@/features/billing/lib/extractionDraft";
import { lineAmount, sumLines } from "@/features/billing/lib/lineMath";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DocumentFileDropzone } from "@/components/ui/file-dropzone";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = {
  patientId: string;
  appointmentId?: string;
};

const emptyRow = (): InvoiceLineItemInput => ({
  description: "",
  category: "other",
  quantity: "1",
  unit_price: "0",
});

export function InvoiceNewPage({ patientId, appointmentId }: Props) {
  const qc = useQueryClient();
  const clinicId = getClinicId();
  const online = useOnlineStatus();
  const [rows, setRows] = useState<InvoiceLineItemInput[]>([emptyRow()]);
  const [draft, setDraft] = useState<BillingExtractionDraft | null>(null);
  const [extractError, setExtractError] = useState<string | null>(null);
  const [extractFile, setExtractFile] = useState<File | null>(null);
  const [extractPreview, setExtractPreview] = useState<string | null>(null);
  const [extracting, setExtracting] = useState(false);

  useEffect(() => {
    return () => {
      if (extractPreview) URL.revokeObjectURL(extractPreview);
    };
  }, [extractPreview]);

  const { data: patient } = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => api.getPatient(patientId),
  });

  const { data: fees } = useQuery({
    queryKey: ["service-fees", clinicId],
    queryFn: () => api.listServiceFees(clinicId!),
    enabled: Boolean(clinicId),
  });

  const save = useMutation({
    mutationFn: async () => {
      const items = rows.filter((r) => r.description.trim());
      const draft = await api.createInvoice(patientId, {
        appointment_id: appointmentId,
        line_items: items.length ? items : undefined,
      });
      const issued = await api.issueInvoice(draft.id);
      return issued;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["invoices", patientId] });
      qc.invalidateQueries({ queryKey: ["patient-balance", patientId] });
    },
  });

  const LINE_CATEGORIES = [
    "consultation",
    "procedure",
    "lab",
    "medicine",
    "other",
  ];

  function addFee(name: string, amount: string, category?: string | null) {
    setRows((prev) => [
      ...prev,
      {
        description: name,
        category:
          category && LINE_CATEGORIES.includes(category) ? category : "other",
        quantity: "1",
        unit_price: amount,
      },
    ]);
  }

  async function handleExtract(file: File | undefined) {
    if (!file) return;
    if (extractPreview) URL.revokeObjectURL(extractPreview);
    const preview = file.type.startsWith("image/")
      ? URL.createObjectURL(file)
      : null;
    setExtractFile(file);
    setExtractPreview(preview);
    setExtractError(null);
    setExtracting(true);
    try {
      const res = await api.extractBillingDocument(patientId, file);
      setDraft(res as BillingExtractionDraft);
    } catch {
      setExtractError("Extraction failed");
    } finally {
      setExtracting(false);
    }
  }

  function clearExtract() {
    if (extractPreview) URL.revokeObjectURL(extractPreview);
    setExtractFile(null);
    setExtractPreview(null);
    setDraft(null);
    setExtractError(null);
  }

  function applyDraft() {
    if (!draft) return;
    setRows((prev) => [...prev, extractionToLineItem(draft)]);
    void api
      .confirmBillingExtraction(patientId, draft.attempt_id)
      .catch(() => {});
    setDraft(null);
  }

  return (
    <div className={pageContainerClass("narrow")}>
      <Link
        to="/dashboard/patients/$patientId"
        params={{ patientId }}
        className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="size-4" />
        {patient?.full_name ?? "Patient"}
      </Link>
      <PageHeader title="New invoice" />

      <Card className="mb-4">
        <CardContent className="flex flex-col gap-1.5 pt-5">
          <Label htmlFor="extract-file">Receipt</Label>
          <DocumentFileDropzone
            id="extract-file"
            accept=".pdf,.png,.jpg,.jpeg,.webp,.txt"
            file={extractFile}
            previewUrl={extractPreview}
            uploading={extracting}
            hasError={Boolean(extractError)}
            emptyLabel="Upload"
            onFileSelect={(file) => void handleExtract(file)}
            onClear={clearExtract}
          />
          {extractError && (
            <p className="mt-2 text-sm text-destructive">{extractError}</p>
          )}
          {draft && (
            <div className="mt-3 flex flex-col gap-2 text-sm">
              {(
                [
                  ["amount", "Amount"],
                  ["date", "Date"],
                  ["provider", "Provider"],
                  ["reference_number", "Reference"],
                ] as const
              ).map(([key, label]) => {
                const field = draft.fields[key];
                return (
                  <div
                    key={key}
                    className={`rounded-lg border p-2.5 ${confidenceClass(field.confidence)}`}
                  >
                    <Label
                      htmlFor={`extract-${key}`}
                      className="text-xs text-muted-foreground"
                    >
                      {label}
                    </Label>
                    <Input
                      id={`extract-${key}`}
                      className="mt-1 bg-card"
                      value={field.value ?? ""}
                      onChange={(e) =>
                        setDraft({
                          ...draft,
                          fields: {
                            ...draft.fields,
                            [key]: { ...field, value: e.target.value },
                          },
                        })
                      }
                    />
                  </div>
                );
              })}
              {draft.source_preview_url && (
                <a
                  href={draft.source_preview_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium text-primary hover:underline"
                >
                  View source
                </a>
              )}
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-fit"
                onClick={applyDraft}
              >
                Add line
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {(fees ?? []).length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {fees?.map((f) => (
            <Button
              key={f.id}
              type="button"
              variant="outline"
              size="sm"
              onClick={() => addFee(f.name, f.amount, f.category)}
            >
              {f.name}
            </Button>
          ))}
        </div>
      )}

      <Card>
        <CardContent className="flex flex-col gap-3 pt-5">
          {rows.map((row, index) => (
            <div
              key={index}
              className="grid gap-2 rounded-lg border border-border p-3 sm:grid-cols-4"
            >
              <Input
                className="sm:col-span-2"
                placeholder={FORM_PLACEHOLDERS.invoiceLine}
                value={row.description}
                onChange={(e) =>
                  setRows((prev) =>
                    prev.map((r, i) =>
                      i === index ? { ...r, description: e.target.value } : r,
                    ),
                  )
                }
              />
              <Input
                type="number"
                min="0"
                step="0.01"
                value={row.unit_price}
                onChange={(e) =>
                  setRows((prev) =>
                    prev.map((r, i) =>
                      i === index ? { ...r, unit_price: e.target.value } : r,
                    ),
                  )
                }
              />
              <span className="flex items-center text-sm text-muted-foreground">
                PHP {lineAmount(row.quantity, row.unit_price)}
              </span>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-fit"
            onClick={() => setRows((prev) => [...prev, emptyRow()])}
          >
            <Plus className="size-4" />
            Add line
          </Button>
        </CardContent>
      </Card>

      <div className="mt-4 flex items-center justify-between">
        <p className="text-sm font-medium text-foreground">
          Total: PHP {sumLines(rows)}
        </p>
        <Button
          type="button"
          disabled={save.isPending || !online}
          onClick={() => save.mutate()}
        >
          {save.isPending ? "Issuing…" : "Issue"}
        </Button>
      </div>
      {!online && (
        <p className="mt-2 text-sm text-warning">
          Billing requires a connection. Reconnect to continue.
        </p>
      )}
      {save.isSuccess && (
        <p className="mt-3 text-sm">Issued {save.data.invoice_number}</p>
      )}
    </div>
  );
}
