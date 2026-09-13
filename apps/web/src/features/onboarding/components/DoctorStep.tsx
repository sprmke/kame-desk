import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { doctorProfileSchema } from "../lib/schemas";
import { useOnboardingMutations } from "../hooks/useOnboarding";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = { onNext: () => void };

export function DoctorStep({ onNext }: Props) {
  const { saveDoctor } = useOnboardingMutations();
  const form = useForm({
    resolver: zodResolver(doctorProfileSchema),
    defaultValues: {
      specialty: "",
      prc_license_number: "",
      consultation_fee: 0,
      follow_up_fee: 0,
    },
  });

  async function onSubmit(values: {
    specialty: string;
    prc_license_number: string;
    consultation_fee: number;
    follow_up_fee?: number;
  }) {
    await saveDoctor.mutateAsync(values);
    onNext();
  }

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={form.handleSubmit(onSubmit)}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="specialty">Specialty</Label>
          <Input id="specialty" {...form.register("specialty")} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="prc_license_number">PRC license</Label>
          <Input
            id="prc_license_number"
            {...form.register("prc_license_number")}
          />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="consultation_fee">Consultation fee</Label>
        <Input
          id="consultation_fee"
          type="number"
          step="0.01"
          {...form.register("consultation_fee")}
        />
      </div>
      <Button
        type="submit"
        className="mt-2 w-fit"
        disabled={saveDoctor.isPending}
      >
        {saveDoctor.isPending ? "Saving…" : "Continue"}
      </Button>
    </form>
  );
}
