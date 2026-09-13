import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Search } from "lucide-react";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChartSearchSkeleton } from "@/components/skeletons/PageSkeletons";
import { EmptyState } from "@/components/EmptyState";

export function ChartSearchPage() {
  const clinicId = getClinicId();
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");

  const { data, isFetching } = useQuery({
    queryKey: ["chart-search", clinicId, submitted],
    queryFn: () => api.chartSearch(clinicId!, submitted),
    enabled: Boolean(clinicId && submitted.length >= 2),
  });

  const hasSubmitted = submitted.length >= 2;
  const items = data?.items ?? [];

  return (
    <Card className="w-full">
      <CardContent className="flex flex-col gap-4 pt-5">
        <form
          className="flex w-full gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            setSubmitted(query.trim());
          }}
        >
          <div className="relative min-w-0 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search SOAP notes, diagnoses, patients"
            />
          </div>
          <Button type="submit" disabled={query.trim().length < 2}>
            Search
          </Button>
        </form>

        {isFetching ? (
          <ChartSearchSkeleton />
        ) : hasSubmitted ? (
          items.length === 0 ? (
            <EmptyState
              icon={Search}
              heading="No matching charts"
              description="Try a different keyword or check the spelling."
              className="py-8"
            />
          ) : (
            <ul className="flex flex-col divide-y divide-border">
              {items.map((item) => (
                <li
                  key={item.soap_note_id}
                  className="py-3 first:pt-0 last:pb-0"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium text-foreground">
                      {item.patient_name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(item.visit_date).toLocaleDateString("en-PH", {
                        timeZone: "Asia/Manila",
                      })}
                    </p>
                  </div>
                  {item.snippet ? (
                    <p className="mt-2 text-sm text-muted-foreground">
                      {item.snippet}
                    </p>
                  ) : null}
                  <Link
                    to="/dashboard/appointments/$appointmentId/soap"
                    params={{ appointmentId: item.appointment_id }}
                    className="mt-2 inline-block text-sm font-medium text-primary hover:underline"
                  >
                    Open v{item.version_number}
                  </Link>
                </li>
              ))}
            </ul>
          )
        ) : (
          <EmptyState
            icon={Search}
            heading="Search charts"
            description="Type a patient name, diagnosis, or SOAP note detail. Use at least 2 characters."
            className="py-8"
          />
        )}
      </CardContent>
    </Card>
  );
}
