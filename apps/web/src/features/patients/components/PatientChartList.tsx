import { Link } from "@tanstack/react-router";
import { ChevronRight, Notebook } from "lucide-react";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import type { PatientChart } from "@/lib/apiClient";

function formatVisitWhen(iso: string) {
  return new Date(iso).toLocaleString("en-PH", {
    timeZone: "Asia/Manila",
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function PatientChartList({
  charts,
  canReadSoap,
}: {
  charts: PatientChart[];
  canReadSoap: boolean;
}) {
  if (charts.length === 0) {
    return (
      <SectionCard>
        <EmptyState icon={Notebook} heading="No charts yet" size="sm" />
      </SectionCard>
    );
  }

  return (
    <SectionCard>
      <ul className="flex flex-col divide-y divide-border">
        {charts.map((chart) => {
          const title =
            chart.diagnosis_primary?.trim() ||
            chart.reason_for_visit?.trim() ||
            "Chart";
          const when = formatVisitWhen(chart.visit_start);
          const body = (
            <>
              <span className="min-w-0">
                <span className="block font-medium text-foreground">
                  {title}
                </span>
                {chart.signed_at ? (
                  <span className="text-muted-foreground">Signed</span>
                ) : null}
              </span>
              <span className="flex shrink-0 items-center gap-1 tabular-nums text-muted-foreground">
                {when}
                {canReadSoap ? (
                  <ChevronRight className="size-4" aria-hidden />
                ) : null}
              </span>
            </>
          );

          return (
            <li key={chart.soap_note_id}>
              {canReadSoap ? (
                <Link
                  to="/dashboard/appointments/$appointmentId/soap"
                  params={{ appointmentId: chart.appointment_id }}
                  aria-label={`Chart: ${title}, ${when}`}
                  className="flex min-h-11 items-center justify-between gap-3 py-2 text-sm native-press hover:bg-secondary"
                >
                  {body}
                </Link>
              ) : (
                <div className="flex min-h-11 items-center justify-between gap-3 py-2 text-sm">
                  {body}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </SectionCard>
  );
}
