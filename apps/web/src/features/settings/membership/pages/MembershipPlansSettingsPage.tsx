import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Wallet } from "lucide-react";
import { api, type MembershipPlan } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { PageHeader } from "@/components/layout/PageHeader";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { ServicesListSkeleton } from "@/components/skeletons/PageSkeletons";
import { EntityList, EntityRow } from "@/components/ui/entity-row";
import { MembershipPlanFormModal } from "@/features/settings/membership/components/MembershipPlanFormModal";

const INTERVAL_LABEL: Record<string, string> = {
  monthly: "Monthly",
  quarterly: "Quarterly",
  annual: "Annual",
};

export function MembershipPlansSettingsPage() {
  const clinicId = getClinicId()!;
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<MembershipPlan | null>(null);

  const {
    data: plans,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["membership-plans", clinicId],
    queryFn: () => api.listMembershipPlans(clinicId),
  });

  const items = plans ?? [];

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(plan: MembershipPlan) {
    setEditing(plan);
    setFormOpen(true);
  }

  return (
    <div>
      <PageHeader
        title="Membership plans"
        actions={
          <Button type="button" onClick={openCreate}>
            <Plus className="size-4" />
            New plan
          </Button>
        }
      />
      <SettingsSection divided={false}>
        <SectionCard>
          {isLoading ? (
            <ServicesListSkeleton />
          ) : isError ? (
            <ErrorState onRetry={() => refetch()} />
          ) : items.length === 0 ? (
            <EmptyState
              icon={Wallet}
              heading="No membership plans yet"
              size="sm"
              action={
                <Button type="button" onClick={openCreate}>
                  New plan
                </Button>
              }
            />
          ) : (
            <EntityList>
              {items.map((plan) => (
                <li key={plan.id} className="px-2">
                  <EntityRow
                    title={plan.name}
                    subtitle={`PHP ${plan.price} · ${INTERVAL_LABEL[plan.billing_interval] ?? plan.billing_interval}`}
                    meta={
                      plan.included_services.length > 0
                        ? plan.included_services
                            .map((s) => `${s.category} x${s.count_per_period}`)
                            .join(", ")
                        : undefined
                    }
                    trailing={
                      <div className="flex items-center gap-2">
                        {!plan.is_active && (
                          <Badge variant="default">Inactive</Badge>
                        )}
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => openEdit(plan)}
                        >
                          Edit
                        </Button>
                      </div>
                    }
                  />
                </li>
              ))}
            </EntityList>
          )}
        </SectionCard>
      </SettingsSection>

      <MembershipPlanFormModal
        clinicId={clinicId}
        plan={editing}
        open={formOpen}
        onOpenChange={setFormOpen}
      />
    </div>
  );
}
