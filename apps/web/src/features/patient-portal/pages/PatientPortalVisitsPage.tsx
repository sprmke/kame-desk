import { useQuery } from "@tanstack/react-query";
import { CalendarDays } from "lucide-react";
import { PatientPortalAppShell } from "@/features/patient-portal/components/PatientPortalAppShell";
import { PortalConsentNotice } from "@/features/patient-portal/components/PortalConsentNotice";
import { patientPortalApi } from "@/features/patient-portal/lib/patientPortalClient";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";

export function PatientPortalVisitsPage({ slug }: { slug: string }) {
  const me = useQuery({
    queryKey: ["portal-me"],
    queryFn: patientPortalApi.getMe,
  });
  const visits = useQuery({
    queryKey: ["portal-visits"],
    queryFn: patientPortalApi.getVisits,
  });

  return (
    <PatientPortalAppShell
      slug={slug}
      clinicName={me.data?.clinic_name}
      patientName={me.data?.full_name}
    >
      <PortalConsentNotice />
      <h1 className="mb-4 text-lg font-semibold text-foreground">
        Your visits
      </h1>
      {visits.isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : visits.isError ? (
        <SectionCard>
          <ErrorState
            heading="Could not load your visits"
            onRetry={() => visits.refetch()}
          />
        </SectionCard>
      ) : visits.data && visits.data.length > 0 ? (
        <div className="flex flex-col gap-3">
          {visits.data.map((v) => (
            <Card key={v.id}>
              <CardContent className="flex items-start justify-between gap-3 py-4">
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {new Date(v.scheduled_start).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Dr. {v.doctor_name}
                    {v.reason_for_visit ? ` — ${v.reason_for_visit}` : ""}
                  </p>
                </div>
                <Badge variant="outline" className="shrink-0">
                  {v.current_visit_status ?? v.appointment_status}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <SectionCard>
          <EmptyState
            icon={CalendarDays}
            heading="No visits yet"
            description="Your visit history will appear here after your first appointment."
          />
        </SectionCard>
      )}
    </PatientPortalAppShell>
  );
}
