import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  SettingsRow,
  SettingsSection,
} from "@/components/settings/SettingsSection";

export function BillingPlanPage() {
  const clinicId = getClinicId();
  const { data: clinic } = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => api.getClinic(clinicId!),
    enabled: Boolean(clinicId),
  });

  const orgId = clinic?.organization_id;
  const { data: org } = useQuery({
    queryKey: ["organization", orgId],
    queryFn: () => api.getOrganization(orgId!),
    enabled: Boolean(orgId),
  });

  const planKey = org?.subscription?.plan_key ?? clinic?.plan_key ?? "starter";
  const status =
    org?.subscription?.status ?? org?.status ?? clinic?.status ?? "trial";

  return (
    <div>
      <PageHeader title="Billing plan" />
      <SettingsSection>
        <SettingsRow label="Plan">
          <span className="capitalize">{planKey}</span>
        </SettingsRow>
        <SettingsRow label="Status">
          <span className="capitalize">{status}</span>
        </SettingsRow>
      </SettingsSection>
      {org?.enrolled_clinics?.length ? (
        <SettingsSection title="Clinics" divided={false}>
          <ul className="space-y-2 text-sm">
            {org.enrolled_clinics.map((row) => (
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
      <Link
        to="/pricing"
        className="text-sm font-medium text-primary hover:underline"
      >
        View plans
      </Link>
    </div>
  );
}
