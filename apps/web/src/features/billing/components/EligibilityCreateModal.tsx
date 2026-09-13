import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type PayerType } from "@/lib/apiClient";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
import {
  ResponsiveModal,
  ResponsiveModalContent,
  ResponsiveModalFooter,
  ResponsiveModalHeader,
  ResponsiveModalTitle,
} from "@/components/ui/responsive-modal";
import { usePatientField } from "@/features/billing/hooks/usePatientField";
import {
  PatientField,
  PayerNameField,
  PayerTypeSelect,
} from "@/features/billing/components/PayerFormFields";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function EligibilityCreateModal({ open, onOpenChange }: Props) {
  const qc = useQueryClient();
  const patient = usePatientField();
  const [payerName, setPayerName] = useState("");
  const [payerType, setPayerType] = useState<PayerType>("hmo");
  const [memberId, setMemberId] = useState("");

  function reset() {
    patient.reset();
    setPayerName("");
    setPayerType("hmo");
    setMemberId("");
  }

  const create = useMutation({
    mutationFn: () =>
      api.createEligibilityCheck({
        patient_id: patient.id,
        payer_name: payerName.trim(),
        payer_type: payerType,
        member_id: memberId.trim() || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["eligibility-checks"] });
      reset();
      onOpenChange(false);
    },
  });

  const canSubmit = Boolean(patient.id) && payerName.trim().length > 0;

  function setOpen(next: boolean) {
    if (!next) reset();
    onOpenChange(next);
  }

  return (
    <ResponsiveModal open={open} onOpenChange={setOpen}>
      <ResponsiveModalContent className="max-w-md">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>New eligibility check</ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <form
          className="flex flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit || create.isPending) return;
            create.mutate();
          }}
        >
          <PatientField id="eligibility-patient" field={patient} />
          <PayerNameField
            id="eligibility-payer"
            label="Payer name"
            value={payerName}
            onChange={setPayerName}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <FieldLabel htmlFor="eligibility-payer-type" label="Payer type" />
              <PayerTypeSelect
                id="eligibility-payer-type"
                value={payerType}
                onChange={(value) => setPayerType(value as PayerType)}
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="eligibility-member" label="Member ID" />
              <Input
                id="eligibility-member"
                value={memberId}
                onChange={(e) => setMemberId(e.target.value)}
                placeholder={FORM_PLACEHOLDERS.memberId}
              />
            </Field>
          </div>
          <FieldError>
            {create.isError ? "Could not request the check." : null}
          </FieldError>
          <ResponsiveModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!canSubmit || create.isPending}>
              {create.isPending ? "Requesting…" : "Request"}
            </Button>
          </ResponsiveModalFooter>
        </form>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}
