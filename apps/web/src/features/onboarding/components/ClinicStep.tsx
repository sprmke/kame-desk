import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { clinicProfileSchema } from "../lib/schemas";
import { useOnboardingMutations } from "../hooks/useOnboarding";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = { onNext: () => void };

export function ClinicStep({ onNext }: Props) {
  const { saveClinic } = useOnboardingMutations();
  const form = useForm({
    resolver: zodResolver(clinicProfileSchema),
    defaultValues: {
      address: "",
      contact_phone: "",
      contact_email: "",
      license_info: "",
      accreditation_info: "",
    },
  });

  async function onSubmit(values: typeof form.formState.defaultValues) {
    await saveClinic.mutateAsync(values as Record<string, unknown>);
    onNext();
  }

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={form.handleSubmit(onSubmit)}
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="address">Address</Label>
        <Input id="address" {...form.register("address")} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="contact_phone">Phone</Label>
          <Input id="contact_phone" {...form.register("contact_phone")} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="contact_email">Email</Label>
          <Input
            id="contact_email"
            type="email"
            {...form.register("contact_email")}
          />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="license_info">License</Label>
        <Input id="license_info" {...form.register("license_info")} />
      </div>
      <Button
        type="submit"
        className="mt-2 w-fit"
        disabled={saveClinic.isPending}
      >
        {saveClinic.isPending ? "Saving…" : "Continue"}
      </Button>
    </form>
  );
}
