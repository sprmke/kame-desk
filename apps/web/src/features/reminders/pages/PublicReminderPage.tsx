import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { CalendarDays, Check, RotateCcw, X } from "lucide-react";
import { api } from "@/lib/apiClient";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";

type Props = { token: string };

export function PublicReminderPage({ token }: Props) {
  const [done, setDone] = useState<string | null>(null);
  const respond = useMutation({
    mutationFn: (action: "confirm" | "cancel" | "reschedule_request") =>
      api.respondToReminder(token, { action }),
    onSuccess: (data) => setDone(data.status),
  });

  if (done) {
    return (
      <AuthLayout title="Appointment">
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-success/10 text-success">
            <Check className="size-6" />
          </span>
          <p className="text-sm text-muted-foreground">{done}</p>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Appointment">
      <div className="flex flex-col gap-3">
        <Button
          type="button"
          size="lg"
          onClick={() => respond.mutate("confirm")}
          disabled={respond.isPending}
        >
          <CalendarDays className="size-4" />
          Confirm
        </Button>
        <Button
          type="button"
          size="lg"
          variant="outline"
          onClick={() => respond.mutate("reschedule_request")}
          disabled={respond.isPending}
        >
          <RotateCcw className="size-4" />
          Request reschedule
        </Button>
        <Button
          type="button"
          size="lg"
          variant="outline"
          className="text-destructive hover:text-destructive"
          onClick={() => respond.mutate("cancel")}
          disabled={respond.isPending}
        >
          <X className="size-4" />
          Cancel
        </Button>
        {respond.isError && (
          <p className="text-sm text-destructive">Link invalid or expired</p>
        )}
      </div>
    </AuthLayout>
  );
}
