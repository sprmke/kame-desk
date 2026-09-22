import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { inviteSchema } from "../lib/schemas";
import { useOnboardingMutations } from "../hooks/useOnboarding";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = { onDone: () => void };

export function InviteStep({ onDone }: Props) {
  const { invite, skipInvite } = useOnboardingMutations();
  const form = useForm<{
    email: string;
    role: "admin" | "doctor" | "reception";
  }>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { email: "", role: "reception" },
  });

  async function onSubmit(values: { email: string; role: string }) {
    await invite.mutateAsync({ email: values.email, role: "reception" });
    onDone();
  }

  async function skip() {
    await skipInvite.mutateAsync();
    onDone();
  }

  return (
    <div className="flex flex-col gap-5">
      <form
        className="flex flex-col gap-4"
        onSubmit={form.handleSubmit(onSubmit)}
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Secretary email</Label>
          <Input id="email" type="email" {...form.register("email")} />
        </div>
        <Button type="submit" className="w-fit" disabled={invite.isPending}>
          {invite.isPending ? "Sending…" : "Send invite"}
        </Button>
      </form>
      <Button
        type="button"
        variant="ghost"
        className="w-fit text-muted-foreground"
        onClick={skip}
        disabled={skipInvite.isPending}
      >
        Skip for now
      </Button>
    </div>
  );
}
