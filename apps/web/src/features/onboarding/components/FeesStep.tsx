import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { feeSchema } from "../lib/schemas";
import { useOnboardingMutations } from "../hooks/useOnboarding";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = { onNext: () => void };

export function FeesStep({ onNext }: Props) {
  const { saveFee } = useOnboardingMutations();
  const form = useForm({
    resolver: zodResolver(feeSchema),
    defaultValues: { name: "Consultation", amount: 0 },
  });

  async function onSubmit(values: { name: string; amount: number }) {
    await saveFee.mutateAsync(values);
    onNext();
  }

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={form.handleSubmit(onSubmit)}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="name">Service name</Label>
          <Input id="name" {...form.register("name")} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="amount">Amount</Label>
          <Input
            id="amount"
            type="number"
            step="0.01"
            {...form.register("amount")}
          />
        </div>
      </div>
      <Button type="submit" className="mt-2 w-fit" disabled={saveFee.isPending}>
        {saveFee.isPending ? "Saving…" : "Continue"}
      </Button>
    </form>
  );
}
