import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ChevronLeft, Plus, TriangleAlert, X } from "lucide-react";
import {
  api,
  type ConflictFlag,
  type PrescriptionItemInput,
} from "@/lib/apiClient";
import { hasConflicts } from "@/features/prescriptions/lib/conflictCheck";
import { conflictFlagKey } from "@/features/prescriptions/lib/flagKey";
import { useOnlineStatus } from "@/lib/onlineStatus";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = {
  patientId: string;
  templateItems?: PrescriptionItemInput[];
};

const emptyRow = (): PrescriptionItemInput => ({
  drug_name: "",
  dosage: "",
  frequency: "",
  duration: "",
  quantity: "",
});

export function PrescriptionNewPage({ patientId, templateItems }: Props) {
  const navigate = useNavigate();
  const online = useOnlineStatus();
  const [rows, setRows] = useState<PrescriptionItemInput[]>(
    templateItems?.length ? templateItems : [emptyRow()],
  );
  const [flags, setFlags] = useState<ConflictFlag[]>([]);
  const [overrideReason, setOverrideReason] = useState("");
  const [explanations, setExplanations] = useState<Record<string, string>>({});
  const [explainingKey, setExplainingKey] = useState<string | null>(null);

  const { data: patient } = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => api.getPatient(patientId),
  });

  const drugNames = rows.map((r) => r.drug_name).filter(Boolean);

  useEffect(() => {
    if (drugNames.length === 0) {
      setFlags([]);
      return;
    }
    void api
      .checkPrescriptionConflicts(patientId, drugNames)
      .then((res) => setFlags(res.flags))
      .catch(() => setFlags([]));
  }, [patientId, drugNames.join("|")]);

  const saveDraft = useMutation({
    mutationFn: async () => {
      const draft = await api.createPrescription(patientId, {
        items: rows.filter((r) => r.drug_name.trim()),
      });
      if (hasConflicts(flags)) {
        if (!overrideReason.trim()) {
          throw new Error("Override reason required");
        }
        await api.issuePrescription(draft.id, {
          override_reason: overrideReason.trim(),
        });
      } else {
        await api.issuePrescription(draft.id, {});
      }
      return draft;
    },
    onSuccess: () =>
      navigate({ to: "/dashboard/patients/$patientId", params: { patientId } }),
  });

  function updateRow(index: number, patch: Partial<PrescriptionItemInput>) {
    setRows((prev) =>
      prev.map((row, i) => (i === index ? { ...row, ...patch } : row)),
    );
  }

  async function explainFlag(flag: ConflictFlag) {
    const key = conflictFlagKey(flag);
    setExplainingKey(key);
    try {
      const res = await api.explainPrescriptionFlag(patientId, flag);
      setExplanations((prev) => ({ ...prev, [key]: res.explanation }));
    } catch {
      setExplanations((prev) => ({
        ...prev,
        [key]: "Could not load explanation.",
      }));
    } finally {
      setExplainingKey(null);
    }
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
      <PageHeader title="New prescription" />

      {flags.some((f) => f.type === "unchecked") && (
        <Card className="mb-4">
          <CardContent className="pt-5 text-sm">
            {flags
              .filter((f) => f.type === "unchecked")
              .map((f) => (
                <p key={f.drug_name}>{f.drug_name}: not checked</p>
              ))}
          </CardContent>
        </Card>
      )}

      {hasConflicts(flags) && (
        <Card className="mb-4 border-warning-500/40 bg-warning-50 dark:bg-warning/10">
          <CardContent className="pt-5">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-warning-700 dark:text-warning-500">
              <TriangleAlert className="size-4" />
              Possible conflicts
            </div>
            {flags
              .filter((f) => f.type !== "unchecked")
              .map((f) => {
                const key = conflictFlagKey(f);
                return (
                  <div key={key} className="mb-3 text-sm">
                    <p className="text-foreground">{f.message}</p>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="mt-1"
                      disabled={explainingKey === key}
                      onClick={() => void explainFlag(f)}
                    >
                      Explain
                    </Button>
                    {explanations[key] && (
                      <p className="mt-1 text-muted-foreground">
                        {explanations[key]}
                      </p>
                    )}
                  </div>
                );
              })}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="override-reason">Override reason</Label>
              <Input
                id="override-reason"
                value={overrideReason}
                placeholder={FORM_PLACEHOLDERS.overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col gap-3">
        {rows.map((row, index) => (
          <Card key={index}>
            <CardContent className="pt-5">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor={`drug-${index}`}>Drug</Label>
                <Input
                  id={`drug-${index}`}
                  value={row.drug_name}
                  placeholder={FORM_PLACEHOLDERS.drugName}
                  onChange={(e) =>
                    updateRow(index, { drug_name: e.target.value })
                  }
                />
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`dosage-${index}`}>Dosage</Label>
                  <Input
                    id={`dosage-${index}`}
                    value={row.dosage ?? ""}
                    placeholder={FORM_PLACEHOLDERS.dosage}
                    onChange={(e) =>
                      updateRow(index, { dosage: e.target.value })
                    }
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`frequency-${index}`}>Frequency</Label>
                  <Input
                    id={`frequency-${index}`}
                    value={row.frequency ?? ""}
                    placeholder={FORM_PLACEHOLDERS.frequency}
                    onChange={(e) =>
                      updateRow(index, { frequency: e.target.value })
                    }
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`duration-${index}`}>Duration</Label>
                  <Input
                    id={`duration-${index}`}
                    value={row.duration ?? ""}
                    placeholder={FORM_PLACEHOLDERS.duration}
                    onChange={(e) =>
                      updateRow(index, { duration: e.target.value })
                    }
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor={`quantity-${index}`}>Quantity</Label>
                  <Input
                    id={`quantity-${index}`}
                    value={row.quantity ?? ""}
                    placeholder={FORM_PLACEHOLDERS.quantity}
                    onChange={(e) =>
                      updateRow(index, { quantity: e.target.value })
                    }
                  />
                </div>
              </div>
              {rows.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="mt-2 text-destructive hover:text-destructive"
                  onClick={() =>
                    setRows((prev) => prev.filter((_, i) => i !== index))
                  }
                >
                  <X className="size-4" />
                  Remove
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
        <Button
          type="button"
          variant="outline"
          className="w-fit"
          onClick={() => setRows((prev) => [...prev, emptyRow()])}
        >
          <Plus className="size-4" />
          Add drug
        </Button>
        <Button
          type="button"
          className="w-fit"
          disabled={
            saveDraft.isPending ||
            rows.every((r) => !r.drug_name.trim()) ||
            !online
          }
          onClick={() => saveDraft.mutate()}
        >
          {saveDraft.isPending ? "Issuing…" : "Issue"}
        </Button>
        {!online && (
          <p className="text-sm text-warning">
            Prescriptions require a connection. Reconnect to continue.
          </p>
        )}
      </div>
    </div>
  );
}
