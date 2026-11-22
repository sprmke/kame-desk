import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { api } from "@/lib/apiClient";
import { useSession } from "@/hooks/useSession";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import {
  SettingsRow,
  SettingsSection,
} from "@/components/settings/SettingsSection";
import { PlanSettingsSkeleton } from "@/components/skeletons/PageSkeletons";
import { EmptyState } from "@/components/EmptyState";

export function OrganizationSettingsPage() {
  const { clinicId, user } = useSession();
  const { data: clinic, isLoading: loadingClinic } = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => api.getClinic(clinicId!),
    enabled: Boolean(clinicId),
  });

  const orgId = clinic?.organization_id;
  const { data: org, isLoading: loadingOrg } = useQuery({
    queryKey: ["organization", orgId],
    queryFn: () => api.getOrganization(orgId!),
    enabled: Boolean(orgId),
  });

  const ownedOrg = user?.organizations?.find((o) => o.is_owner);

  if (loadingClinic || loadingOrg) {
    return (
      <div>
        <PageHeader title="Organization" />
        <PlanSettingsSkeleton />
      </div>
    );
  }

  if (!ownedOrg && !org) {
    return (
      <div>
        <PageHeader title="Organization" />
        <EmptyState icon={Building2} heading="No organization" size="sm" />
      </div>
    );
  }

  const displayOrg =
    org ??
    (ownedOrg
      ? { ...ownedOrg, enrolled_clinics: [], subscription: null }
      : null);
  if (!displayOrg) return null;

  return (
    <div>
      <PageHeader title="Organization" />
      <SettingsSection>
        <SettingsRow label="Name">{displayOrg.name}</SettingsRow>
        {displayOrg.subscription ? (
          <SettingsRow label="Plan">
            <span className="capitalize">
              {displayOrg.subscription.plan_key} ·{" "}
              {displayOrg.subscription.status}
            </span>
          </SettingsRow>
        ) : null}
      </SettingsSection>
      {displayOrg.enrolled_clinics?.length ? (
        <SettingsSection title="Clinics" divided={false}>
          <ul className="space-y-2 text-sm">
            {displayOrg.enrolled_clinics.map((row) => (
              <li
                key={row.clinic_id}
                className="flex items-center justify-between gap-2 py-2"
              >
                <span>{row.clinic_name}</span>
                <span className="text-muted-foreground capitalize">
                  {row.status === "pending_enrollment" ? "Pending" : row.status}
                </span>
              </li>
            ))}
          </ul>
        </SettingsSection>
      ) : null}
      {ownedOrg ? (
        <Button asChild>
          <Link to="/dashboard/settings/organization/clinics/new">
            Add clinic
          </Link>
        </Button>
      ) : null}
    </div>
  );
}
