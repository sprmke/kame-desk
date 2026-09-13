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

export function RoomCreateModal({ clinicId, open, onOpenChange }: Props) {
  const qc = useQueryClient();
  const [name, setName] = useState("");

  function reset() {
    setName("");
  }

  const create = useMutation({
    mutationFn: () => api.createRoom(clinicId, { name: name.trim() }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["rooms", clinicId] });
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
          <ResponsiveModalTitle>New room</ResponsiveModalTitle>
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
            <FieldLabel htmlFor="room-name" label="Name" required />
            <Input
              id="room-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={FORM_PLACEHOLDERS.roomName}
            />
          </Field>
          <FieldError>
            {create.isError ? "Could not save the room." : null}
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
