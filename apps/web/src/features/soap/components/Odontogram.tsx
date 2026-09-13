import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { History, Plus } from "lucide-react";
import {
  api,
  type ToothChartEntry,
  type ToothCondition,
  type ToothEntryStatus,
  type ToothSurface,
} from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ResponsiveModal,
  ResponsiveModalContent,
  ResponsiveModalFooter,
  ResponsiveModalHeader,
  ResponsiveModalTitle,
} from "@/components/ui/responsive-modal";

const UPPER_ARCH = [
  18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28,
];
const LOWER_ARCH = [
  48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38,
];

const CONDITIONS: ToothCondition[] = [
  "sound",
  "caries",
  "filled",
  "missing",
  "crown",
  "root_canal",
  "extraction_planned",
  "impacted",
  "fractured",
];

const SURFACES: ToothSurface[] = [
  "mesial",
  "distal",
  "occlusal",
  "buccal",
  "lingual",
  "incisal",
];

const CONDITION_LABEL: Record<ToothCondition, string> = {
  sound: "Sound",
  caries: "Caries",
  filled: "Filled",
  missing: "Missing",
  crown: "Crown",
  root_canal: "Root canal",
  extraction_planned: "Extraction planned",
  impacted: "Impacted",
  fractured: "Fractured",
};

const CONDITION_BADGE: Record<
  ToothCondition,
  "default" | "success" | "warning" | "error" | "info" | "brand"
> = {
  sound: "default",
  caries: "error",
  filled: "info",
  missing: "default",
  crown: "brand",
  root_canal: "warning",
  extraction_planned: "warning",
  impacted: "error",
  fractured: "error",
};

const CONDITION_TOOTH_CLASS: Record<ToothCondition, string> = {
  sound: "border-border bg-card text-foreground",
  caries:
    "border-error-500 bg-error-50 text-error-700 dark:bg-destructive/15 dark:text-destructive",
  filled:
    "border-info-500 bg-info-50 text-info-700 dark:bg-info-500/15 dark:text-info-500",
  missing: "border-border bg-muted text-muted-foreground line-through",
  crown:
    "border-brand-500 bg-brand-50 text-brand-700 dark:bg-accent dark:text-accent-foreground",
  root_canal:
    "border-warning-500 bg-warning-50 text-warning-700 dark:bg-warning/15 dark:text-warning",
  extraction_planned:
    "border-warning-500 bg-warning-50 text-warning-700 dark:bg-warning/15 dark:text-warning",
  impacted:
    "border-error-500 bg-error-50 text-error-700 dark:bg-destructive/15 dark:text-destructive",
  fractured:
    "border-error-500 bg-error-50 text-error-700 dark:bg-destructive/15 dark:text-destructive",
};

function latestByTooth(
  entries: ToothChartEntry[],
): Map<number, ToothChartEntry> {
  const map = new Map<number, ToothChartEntry>();
  for (const entry of entries) {
    const current = map.get(entry.tooth_number);
    if (!current || new Date(entry.noted_at) > new Date(current.noted_at)) {
      map.set(entry.tooth_number, entry);
    }
  }
  return map;
}

function ToothButton({
  tooth,
  latest,
  selected,
  onClick,
}: {
  tooth: number;
  latest: ToothChartEntry | undefined;
  selected: boolean;
  onClick: () => void;
}) {
  const isMissing = latest?.condition === "missing";
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-11 min-w-11 flex-col items-center justify-center rounded-md border text-xs font-medium native-press",
        latest
          ? CONDITION_TOOTH_CLASS[latest.condition]
          : "border-border bg-card text-foreground",
        latest?.status === "planned" && "border-dashed",
        selected && "ring-2 ring-primary ring-offset-1",
      )}
      aria-label={`Tooth ${tooth}${latest ? `, ${CONDITION_LABEL[latest.condition]}` : ""}`}
      aria-pressed={selected}
    >
      <span>{tooth}</span>
      {isMissing && <span className="text-[10px] leading-none">×</span>}
    </button>
  );
}

type Props = {
  patientId: string;
  appointmentId?: string;
  soapNoteId?: string;
  disabled?: boolean;
};

export function Odontogram({
  patientId,
  appointmentId,
  soapNoteId,
  disabled,
}: Props) {
  const qc = useQueryClient();
  const [selectedTooth, setSelectedTooth] = useState<number | null>(null);
  const [surface, setSurface] = useState<string>("none");
  const [condition, setCondition] = useState<ToothCondition>("caries");
  const [status, setStatus] = useState<ToothEntryStatus>("existing");
  const [showHistory, setShowHistory] = useState(false);
  const [invoiceEntry, setInvoiceEntry] = useState<ToothChartEntry | null>(
    null,
  );
  const [invoiceDescription, setInvoiceDescription] = useState("");
  const [invoiceAmount, setInvoiceAmount] = useState("");
  const [addedInvoiceId, setAddedInvoiceId] = useState<string | null>(null);

  const { data: entries } = useQuery({
    queryKey: ["tooth-chart", patientId],
    queryFn: () => api.listToothChart(patientId),
  });

  const items = entries ?? [];
  const latestMap = useMemo(() => latestByTooth(items), [items]);
  const plannedEntries = useMemo(
    () => items.filter((e) => e.status === "planned"),
    [items],
  );
  const selectedHistory = useMemo(
    () =>
      selectedTooth === null
        ? []
        : items.filter((e) => e.tooth_number === selectedTooth),
    [items, selectedTooth],
  );
  const selectedIsMissing =
    selectedTooth !== null &&
    latestMap.get(selectedTooth)?.condition === "missing";

  const create = useMutation({
    mutationFn: () =>
      api.createToothChartEntry(patientId, {
        appointment_id: appointmentId,
        soap_note_id: soapNoteId,
        tooth_number: selectedTooth!,
        surface:
          selectedIsMissing || surface === "none"
            ? undefined
            : (surface as ToothSurface),
        condition,
        status,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tooth-chart", patientId] });
      setSurface("none");
      setCondition("caries");
      setStatus("existing");
    },
  });

  const addToInvoice = useMutation({
    mutationFn: () =>
      api.addToothChartEntryToInvoice(patientId, invoiceEntry!.id, {
        description: invoiceDescription.trim(),
        amount: invoiceAmount,
        appointment_id: appointmentId,
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["tooth-chart", patientId] });
      setAddedInvoiceId(data.invoice_id);
      setInvoiceEntry(null);
      setInvoiceDescription("");
      setInvoiceAmount("");
    },
  });

  function openInvoiceDialog(entry: ToothChartEntry) {
    setAddedInvoiceId(null);
    setInvoiceEntry(entry);
    setInvoiceDescription(
      `Tooth ${entry.tooth_number} — ${CONDITION_LABEL[entry.condition]}`,
    );
    setInvoiceAmount("");
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <Label>Odontogram</Label>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setShowHistory((v) => !v)}
        >
          <History className="size-3.5" />
          {showHistory ? "Hide history" : "History"}
        </Button>
      </div>

      <div className="flex flex-col gap-2 overflow-x-auto rounded-lg border border-border p-3">
        <div className="flex justify-between gap-1">
          {UPPER_ARCH.map((tooth, idx) => (
            <div key={tooth} className={idx === 8 ? "ml-2" : undefined}>
              <ToothButton
                tooth={tooth}
                latest={latestMap.get(tooth)}
                selected={selectedTooth === tooth}
                onClick={() => setSelectedTooth(tooth)}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between gap-1">
          {LOWER_ARCH.map((tooth, idx) => (
            <div key={tooth} className={idx === 8 ? "ml-2" : undefined}>
              <ToothButton
                tooth={tooth}
                latest={latestMap.get(tooth)}
                selected={selectedTooth === tooth}
                onClick={() => setSelectedTooth(tooth)}
              />
            </div>
          ))}
        </div>
      </div>

      {selectedTooth !== null && (
        <div className="flex flex-col gap-3 rounded-lg border border-border p-3">
          <p className="text-sm font-medium text-foreground">
            Tooth {selectedTooth}
          </p>

          {selectedHistory.length > 0 && (
            <ul className="flex flex-col gap-1 text-sm text-muted-foreground">
              {selectedHistory.map((entry) => (
                <li
                  key={entry.id}
                  className="flex flex-wrap items-center gap-2"
                >
                  <Badge variant={CONDITION_BADGE[entry.condition]}>
                    {CONDITION_LABEL[entry.condition]}
                  </Badge>
                  {entry.surface && <span>{entry.surface}</span>}
                  <span className="text-xs">
                    {new Date(entry.noted_at).toLocaleDateString()}
                  </span>
                  {entry.status === "planned" && !disabled && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => openInvoiceDialog(entry)}
                    >
                      Add to invoice
                    </Button>
                  )}
                  {entry.status === "completed" && (
                    <Badge variant="success">Completed</Badge>
                  )}
                </li>
              ))}
            </ul>
          )}

          {selectedIsMissing && (
            <p className="text-xs text-muted-foreground">
              This tooth is marked missing — surface-level charting is disabled.
            </p>
          )}

          {!disabled && (
            <div className="grid gap-2 sm:grid-cols-3">
              <Select
                value={selectedIsMissing ? "none" : surface}
                onValueChange={setSurface}
                disabled={selectedIsMissing}
              >
                <SelectTrigger aria-label="Surface">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Whole tooth</SelectItem>
                  {SURFACES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={condition}
                onValueChange={(v) => setCondition(v as ToothCondition)}
              >
                <SelectTrigger aria-label="Condition">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CONDITIONS.map((c) => (
                    <SelectItem key={c} value={c}>
                      {CONDITION_LABEL[c]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={status}
                onValueChange={(v) => setStatus(v as ToothEntryStatus)}
              >
                <SelectTrigger aria-label="Status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="existing">Existing</SelectItem>
                  <SelectItem value="planned">Planned</SelectItem>
                </SelectContent>
              </Select>
              <Button
                type="button"
                className="sm:col-span-3"
                disabled={create.isPending}
                onClick={() => create.mutate()}
              >
                <Plus className="size-4" />
                Add finding
              </Button>
            </div>
          )}
        </div>
      )}

      {showHistory && (
        <div className="flex flex-col gap-1 rounded-lg border border-border p-3 text-sm">
          {items.length === 0 ? (
            <p className="text-muted-foreground">No tooth chart entries yet.</p>
          ) : (
            items.map((entry) => (
              <div
                key={entry.id}
                className="flex flex-wrap items-center gap-2 border-b border-border py-1.5 last:border-0"
              >
                <span className="font-medium text-foreground">
                  Tooth {entry.tooth_number}
                </span>
                <Badge variant={CONDITION_BADGE[entry.condition]}>
                  {CONDITION_LABEL[entry.condition]}
                </Badge>
                {entry.surface && (
                  <span className="text-muted-foreground">{entry.surface}</span>
                )}
                <span className="text-xs text-muted-foreground">
                  {new Date(entry.noted_at).toLocaleString()}
                </span>
              </div>
            ))
          )}
        </div>
      )}

      {plannedEntries.length > 0 && (
        <div className="flex flex-col gap-2 rounded-lg border border-border p-3">
          <Label>Treatment plan</Label>
          <ul className="flex flex-col gap-2">
            {plannedEntries.map((entry) => (
              <li
                key={entry.id}
                className="flex flex-wrap items-center justify-between gap-2 text-sm"
              >
                <span>
                  Tooth {entry.tooth_number} —{" "}
                  {CONDITION_LABEL[entry.condition]}
                </span>
                {!disabled && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => openInvoiceDialog(entry)}
                  >
                    Add to invoice
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {items.length === 0 && plannedEntries.length === 0 && !showHistory && (
        <SectionCard>
          <EmptyState
            icon={History}
            size="sm"
            heading="No teeth charted yet for this patient"
          />
        </SectionCard>
      )}

      {addedInvoiceId && (
        <p className="text-sm text-success">
          Added to invoice.{" "}
          <Link
            to="/dashboard/patients/$patientId/invoices/$invoiceId"
            params={{ patientId, invoiceId: addedInvoiceId }}
            className="font-medium underline"
          >
            View invoice
          </Link>
        </p>
      )}

      <ResponsiveModal
        open={invoiceEntry !== null}
        onOpenChange={(open) => !open && setInvoiceEntry(null)}
      >
        <ResponsiveModalContent className="max-w-md">
          <ResponsiveModalHeader>
            <ResponsiveModalTitle>
              Add procedure to invoice
            </ResponsiveModalTitle>
          </ResponsiveModalHeader>
          <form
            className="flex flex-col gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              if (
                !invoiceDescription.trim() ||
                !invoiceAmount ||
                addToInvoice.isPending
              )
                return;
              addToInvoice.mutate();
            }}
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="invoice-desc">Description</Label>
              <Input
                id="invoice-desc"
                value={invoiceDescription}
                onChange={(e) => setInvoiceDescription(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="invoice-amount">Amount</Label>
              <Input
                id="invoice-amount"
                type="number"
                min={0}
                step="0.01"
                value={invoiceAmount}
                onChange={(e) => setInvoiceAmount(e.target.value)}
                placeholder="0.00"
              />
            </div>
            <ResponsiveModalFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setInvoiceEntry(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={
                  !invoiceDescription.trim() ||
                  !invoiceAmount ||
                  addToInvoice.isPending
                }
              >
                {addToInvoice.isPending ? "Adding…" : "Add"}
              </Button>
            </ResponsiveModalFooter>
          </form>
        </ResponsiveModalContent>
      </ResponsiveModal>
    </div>
  );
}
