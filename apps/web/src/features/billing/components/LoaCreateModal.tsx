import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/forms/Field";
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
} from "@/features/billing/components/PayerFormFields";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function LoaCreateModal({ open, onOpenChange }: Props) {
  const qc = useQueryClient();
  const patient = usePatientField();
  const [hmoName, setHmoName] = useState("");

  function reset() {
    patient.reset();
    setHmoName("");
  }

  const create = useMutation({
    mutationFn: () =>
      api.createLoaRequest({
        patient_id: patient.id,
        hmo_name: hmoName.trim(),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["loa-requests"] });
      reset();
      onOpenChange(false);
    },
  });

  const canSubmit = Boolean(patient.id) && hmoName.trim().length > 0;

  function setOpen(next: boolean) {
    if (!next) reset();
    onOpenChange(next);
  }

  return (
    <ResponsiveModal open={open} onOpenChange={setOpen}>
      <ResponsiveModalContent className="max-w-md">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>New LOA request</ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <form
          className="flex flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit || create.isPending) return;
            create.mutate();
          }}
        >
          <PatientField id="loa-patient" field={patient} />
          <PayerNameField
            id="loa-hmo"
            label="HMO / payer"
            value={hmoName}
            onChange={setHmoName}
          />
          <FieldError>
            {create.isError ? "Could not save the request." : null}
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
