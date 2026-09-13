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

export function ClaimCreateModal({ open, onOpenChange }: Props) {
  const qc = useQueryClient();
  const patient = usePatientField();
  const [provider, setProvider] = useState("");
  const [payerType, setPayerType] = useState<PayerType>("hmo");
  const [memberId, setMemberId] = useState("");
  const [amount, setAmount] = useState("");

  function reset() {
    patient.reset();
    setProvider("");
    setPayerType("hmo");
    setMemberId("");
    setAmount("");
  }

  const create = useMutation({
    mutationFn: () =>
      api.createClaim({
        patient_id: patient.id,
        provider: provider.trim(),
        payer_type: payerType,
        member_id: memberId.trim() || undefined,
        amount,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["claims"] });
      reset();
      onOpenChange(false);
    },
  });

  const canSubmit =
    Boolean(patient.id) &&
    provider.trim().length > 0 &&
    amount.trim().length > 0;

  function setOpen(next: boolean) {
    if (!next) reset();
    onOpenChange(next);
  }

  return (
    <ResponsiveModal open={open} onOpenChange={setOpen}>
      <ResponsiveModalContent className="max-w-md">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>New claim</ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <form
          className="flex flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit || create.isPending) return;
            create.mutate();
          }}
        >
          <PatientField id="claim-patient" field={patient} />
          <PayerNameField
            id="claim-provider"
            label="HMO / payer name"
            value={provider}
            onChange={setProvider}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <FieldLabel htmlFor="claim-payer-type" label="Payer type" />
              <PayerTypeSelect
                id="claim-payer-type"
                value={payerType}
                onChange={(value) => setPayerType(value as PayerType)}
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="claim-member" label="Member ID" />
              <Input
                id="claim-member"
                value={memberId}
                onChange={(e) => setMemberId(e.target.value)}
                placeholder={FORM_PLACEHOLDERS.memberId}
              />
            </Field>
          </div>
          <Field>
            <FieldLabel htmlFor="claim-amount" label="Amount" required />
            <Input
              id="claim-amount"
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
            />
          </Field>
          <FieldError>
            {create.isError ? "Could not save the claim." : null}
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
              {create.isPending ? "Saving…" : "Save"}
            </Button>
          </ResponsiveModalFooter>
        </form>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}
