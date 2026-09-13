import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { setActiveClinic } from "@/lib/auth";
import { useSession } from "@/hooks/useSession";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function CreateClinicPage() {
  const navigate = useNavigate();
  const { clinicId, user } = useSession();
  const ownedOrg = user?.organizations?.find((o) => o.is_owner);

  const { data: clinic } = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => api.getClinic(clinicId!),
    enabled: Boolean(clinicId),
  });

  const orgId = ownedOrg?.id ?? clinic?.organization_id;
  const [name, setName] = useState("");

  const createClinic = useMutation({
    mutationFn: () => api.createClinicUnderOrg(orgId!, { name: name.trim() }),
    onSuccess: (res) => {
      setActiveClinic(res.clinic_id);
      navigate({ to: "/onboarding" });
    },
  });

  if (!orgId) return null;

  return (
    <div>
      <PageHeader title="Add clinic" />
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          if (!name.trim()) return;
          createClinic.mutate();
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="clinic-name">Clinic name</Label>
          <Input
            id="clinic-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        {createClinic.isError ? (
          <p className="text-sm text-destructive">Could not create clinic.</p>
        ) : null}
        <Button type="submit" disabled={createClinic.isPending || !name.trim()}>
          Create
        </Button>
      </form>
    </div>
  );
}
