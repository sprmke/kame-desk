import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { api } from "@/lib/apiClient";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { EmptyState } from "@/components/EmptyState";

export function DocumentGeneratePage() {
  const [q, setQ] = useState("");
  const { data } = useQuery({
    queryKey: ["patients", q],
    queryFn: () => api.listPatients({ q, page_size: 12 }),
    enabled: q.trim().length >= 2,
  });

  const results = data?.items ?? [];
  const showResults = q.trim().length >= 2;

  return (
    <Card className="w-full">
      <CardContent className="flex flex-col gap-3 pt-5">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="doc-patient">Patient</Label>
          <Input
            id="doc-patient"
            value={q}
            placeholder={FORM_PLACEHOLDERS.searchPatients}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        {showResults && results.length === 0 ? (
          <EmptyState
            icon={Search}
            heading="No patients found"
            description="Try a different name, contact number, or patient ID."
            size="sm"
          />
        ) : (
          <ul className="flex flex-col divide-y divide-border text-sm">
            {results.map((p) => (
              <li key={p.id} className="py-2 first:pt-0 last:pb-0">
                <Link
                  to="/dashboard/patients/$patientId/documents/new"
                  params={{ patientId: p.id }}
                  className="font-medium text-primary hover:underline"
                >
                  {p.full_name}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
