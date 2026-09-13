import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Check } from "lucide-react";
import { api } from "@/lib/apiClient";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type Props = { token: string };

const SCORES = Array.from({ length: 11 }, (_, i) => i);

export function PublicNpsPage({ token }: Props) {
  const [score, setScore] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [done, setDone] = useState(false);

  const respond = useMutation({
    mutationFn: () =>
      api.respondToNps(token, {
        score: score!,
        comment: comment.trim() || undefined,
      }),
    onSuccess: () => setDone(true),
  });

  if (done) {
    return (
      <AuthLayout title="Thank you">
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-success/10 text-success">
            <Check className="size-6" />
          </span>
          <p className="text-sm text-muted-foreground">
            Your feedback has been recorded.
          </p>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="How likely are you to recommend us?">
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-11 gap-1">
          {SCORES.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setScore(value)}
              className={cn(
                "flex h-10 items-center justify-center rounded-md border text-sm font-medium native-press",
                score === value
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border text-foreground hover:bg-muted",
              )}
            >
              {value}
            </button>
          ))}
        </div>
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Not likely</span>
          <span>Very likely</span>
        </div>
        <Textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Anything you'd like to add? (optional)"
          rows={3}
        />
        <Button
          type="button"
          size="lg"
          disabled={score === null || respond.isPending}
          onClick={() => respond.mutate()}
        >
          Submit
        </Button>
        {respond.isError && (
          <p className="text-sm text-destructive">Link invalid or expired</p>
        )}
      </div>
    </AuthLayout>
  );
}
