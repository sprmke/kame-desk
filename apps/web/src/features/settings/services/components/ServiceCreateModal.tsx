import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
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

type Props = {
  clinicId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function ServiceCreateModal({ clinicId, open, onOpenChange }: Props) {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("");
  const [duration, setDuration] = useState("");

  function reset() {
    setName("");
    setAmount("");
    setCategory("");
    setDuration("");
  }

  const create = useMutation({
    mutationFn: () =>
      api.createServiceFee(clinicId, {
        name: name.trim(),
        amount: Number(amount),
        category: category.trim() || undefined,
        duration_minutes: duration ? Number(duration) : undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["service-fees", clinicId] });
      reset();
      onOpenChange(false);
    },
  });

  const canSubmit = name.trim().length > 0 && amount.trim().length > 0;

  function setOpen(next: boolean) {
    if (!next) reset();
    onOpenChange(next);
  }

  return (
    <ResponsiveModal open={open} onOpenChange={setOpen}>
      <ResponsiveModalContent className="max-w-md">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>New service</ResponsiveModalTitle>
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
            <FieldLabel htmlFor="fee-name" label="Name" required />
            <Input
              id="fee-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={FORM_PLACEHOLDERS.serviceName}
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <FieldLabel htmlFor="fee-amount" label="Amount" required />
              <Input
                id="fee-amount"
                type="number"
                min={0}
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="fee-duration" label="Minutes" />
              <Input
                id="fee-duration"
                type="number"
                min={5}
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                placeholder="30"
              />
            </Field>
          </div>
          <Field>
            <FieldLabel htmlFor="fee-category" label="Category" />
            <Input
              id="fee-category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder={FORM_PLACEHOLDERS.serviceCategory}
            />
          </Field>
          <FieldError>
            {create.isError ? "Could not save the service." : null}
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
