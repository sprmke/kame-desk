import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type Props = { appointmentId: string };

export function VisitSummaryPanel({ appointmentId }: Props) {
  const qc = useQueryClient();
  const [edited, setEdited] = useState("");

  const { data: summary } = useQuery({
    queryKey: ["visit-summary", appointmentId],
    queryFn: () => api.getVisitSummary(appointmentId),
  });

  const approve = useMutation({
    mutationFn: () =>
      api.approveVisitSummary(appointmentId, edited || summary?.generated_text),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["visit-summary", appointmentId] }),
  });

  const suppress = useMutation({
    mutationFn: () => api.suppressVisitSummary(appointmentId),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["visit-summary", appointmentId] }),
  });

  if (
    !summary ||
    summary.status === "sent" ||
    summary.status === "suppressed"
  ) {
    return null;
  }

  const text = edited || summary.edited_text || summary.generated_text;
  const canSend = Boolean(text.trim());

  return (
    <div className="mt-2.5 rounded-lg border border-border bg-secondary/40 p-2.5 text-sm">
      <p className="mb-2 font-medium text-foreground">Visit summary</p>
      {summary.generation_failed ? (
        <p className="mb-2 text-muted-foreground">
          AI summary unavailable. Write it manually.
        </p>
      ) : null}
      <Textarea
        className="mb-2 bg-card"
        rows={4}
        value={text}
        onChange={(e) => setEdited(e.target.value)}
      />
      <div className="flex gap-2">
        <Button
          type="button"
          size="sm"
          disabled={approve.isPending || !canSend}
          onClick={() => approve.mutate()}
        >
          Send
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={suppress.isPending}
          onClick={() => suppress.mutate()}
        >
          Suppress
        </Button>
      </div>
    </div>
  );
}
