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
import { PayerTypeSelect } from "@/features/billing/components/PayerFormFields";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function PayerCreateModal({ open, onOpenChange }: Props) {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [payerType, setPayerType] = useState<PayerType>("hmo");

  function reset() {
    setName("");
    setPayerType("hmo");
  }

  const create = useMutation({
    mutationFn: () =>
      api.createPayer({ name: name.trim(), payer_type: payerType }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["payers"] });
      reset();
      onOpenChange(false);
    },
  });

  const canSubmit = name.trim().length > 0;

  function setOpen(next: boolean) {
    if (!next) reset();
    onOpenChange(next);
  }

  return (
    <ResponsiveModal open={open} onOpenChange={setOpen}>
      <ResponsiveModalContent className="max-w-sm">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>New payer</ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <form
          className="flex flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit || create.isPending) return;
            create.mutate();
          }}
        >
          <Field>
            <FieldLabel htmlFor="payer-name" label="Name" required />
            <Input
              id="payer-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={FORM_PLACEHOLDERS.hmo}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="payer-type" label="Type" />
            <PayerTypeSelect
              id="payer-type"
              value={payerType}
              onChange={(value) => setPayerType(value as PayerType)}
            />
          </Field>
          <FieldError>
            {create.isError ? "Could not save the payer." : null}
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
