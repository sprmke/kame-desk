import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { api, type PayerType } from "@/lib/apiClient";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/EmptyState";
import { Field } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const PAYER_TYPES: { value: PayerType; label: string }[] = [
  { value: "hmo", label: "HMO" },
  { value: "philhealth", label: "PhilHealth" },
];

export function PatientEligibilityCard({ patientId }: { patientId: string }) {
  const qc = useQueryClient();
  const [payerName, setPayerName] = useState("");
  const [payerType, setPayerType] = useState<PayerType>("hmo");
  const [memberId, setMemberId] = useState("");

  const { data } = useQuery({
    queryKey: ["eligibility-checks", patientId],
    queryFn: () => api.listEligibilityChecks({ patient_id: patientId }),
  });

  const create = useMutation({
    mutationFn: () =>
      api.createEligibilityCheck({
        patient_id: patientId,
        payer_name: payerName.trim(),
        payer_type: payerType,
        member_id: memberId || undefined,
      }),
    onSuccess: () => {
      setPayerName("");
      setMemberId("");
      qc.invalidateQueries({ queryKey: ["eligibility-checks", patientId] });
    },
  });

  const latest = data?.items[0];

  return (
    <Card>
      <CardHeader>
        <CardTitle>HMO / PhilHealth eligibility</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {latest ? (
          <div className="flex items-center justify-between text-sm">
            <div>
              <span className="font-medium text-foreground">
                {latest.payer_name}
              </span>
              <span className="text-muted-foreground">
                {" "}
                ({latest.payer_type})
              </span>
              {latest.verified_amount ? (
                <div className="text-muted-foreground">
                  Verified PHP {latest.verified_amount}
                </div>
              ) : null}
            </div>
            <Badge
              variant={latest.status === "verified" ? "default" : "outline"}
            >
              {latest.status}
            </Badge>
          </div>
        ) : (
          <EmptyState
            icon={ShieldCheck}
            heading="No eligibility check on file"
            size="sm"
          />
        )}

        <div className="grid gap-2 sm:grid-cols-3">
          <Field>
            <FieldLabel htmlFor="patient-elig-payer" label="Payer" />
            <Input
              id="patient-elig-payer"
              value={payerName}
              onChange={(e) => setPayerName(e.target.value)}
              placeholder={FORM_PLACEHOLDERS.hmo}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="patient-elig-type" label="Type" />
            <Select
              value={payerType}
              onValueChange={(v) => setPayerType(v as PayerType)}
            >
              <SelectTrigger id="patient-elig-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PAYER_TYPES.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field>
            <FieldLabel htmlFor="patient-elig-member" label="Member ID" />
            <Input
              id="patient-elig-member"
              value={memberId}
              onChange={(e) => setMemberId(e.target.value)}
              placeholder={FORM_PLACEHOLDERS.memberId}
            />
          </Field>
        </div>
        <Button
          type="button"
          className="w-fit"
          disabled={create.isPending || !payerName.trim()}
          onClick={() => create.mutate()}
        >
          Request check
        </Button>
      </CardContent>
    </Card>
  );
}
