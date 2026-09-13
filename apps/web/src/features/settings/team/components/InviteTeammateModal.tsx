import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/apiClient";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { inviteSchema } from "@/features/onboarding/lib/schemas";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type InviteValues = {
  email: string;
  role: "admin" | "doctor" | "reception";
};

type Props = {
  clinicId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function InviteTeammateModal({ clinicId, open, onOpenChange }: Props) {
  const qc = useQueryClient();
  const form = useForm<InviteValues>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { email: "", role: "reception" },
  });

  const invite = useMutation({
    mutationFn: (body: InviteValues) => api.createInvitation(clinicId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["invitations", clinicId] });
      form.reset();
      onOpenChange(false);
    },
  });

  function setOpen(next: boolean) {
    if (!next) form.reset();
    onOpenChange(next);
  }

  return (
    <ResponsiveModal open={open} onOpenChange={setOpen}>
      <ResponsiveModalContent className="max-w-sm">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>Invite a teammate</ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <form
          className="flex flex-col gap-4"
          onSubmit={form.handleSubmit((v) => invite.mutate(v))}
        >
          <Field>
            <FieldLabel htmlFor="invite-email" label="Email" required />
            <Input
              id="invite-email"
              type="email"
              placeholder={FORM_PLACEHOLDERS.email}
              {...form.register("email")}
            />
            <FieldError>{form.formState.errors.email?.message}</FieldError>
          </Field>
          <Field>
            <FieldLabel htmlFor="invite-role" label="Role" />
            <Select
              value={form.watch("role")}
              onValueChange={(v) =>
                form.setValue("role", v as InviteValues["role"])
              }
            >
              <SelectTrigger id="invite-role" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="reception">Reception</SelectItem>
                <SelectItem value="doctor">Doctor</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          <FieldError>
            {invite.error instanceof Error ? invite.error.message : null}
          </FieldError>
          <ResponsiveModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={invite.isPending}>
              {invite.isPending ? "Sending…" : "Send invite"}
            </Button>
          </ResponsiveModalFooter>
        </form>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}
