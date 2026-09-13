import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, CircleDollarSign } from "lucide-react";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { PageHeader } from "@/components/layout/PageHeader";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { ServicesListSkeleton } from "@/components/skeletons/PageSkeletons";
import { EntityList, EntityRow } from "@/components/ui/entity-row";
import { ServiceCreateModal } from "@/features/settings/services/components/ServiceCreateModal";

export function ServicesSettingsPage() {
  const clinicId = getClinicId()!;
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);

  const {
    data: fees,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["service-fees", clinicId],
    queryFn: () => api.listServiceFees(clinicId),
  });

  const remove = useMutation({
    mutationFn: (feeId: string) => api.deleteServiceFee(clinicId, feeId),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["service-fees", clinicId] }),
  });

  const items = fees ?? [];

  return (
    <div>
      <PageHeader
        title="Services and fees"
        actions={
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" />
            New service
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
              icon={CircleDollarSign}
              heading="No services yet"
              size="sm"
              action={
                <Button type="button" onClick={() => setCreateOpen(true)}>
                  New service
                </Button>
              }
            />
          ) : (
            <EntityList>
              {items.map((fee) => (
                <li key={fee.id} className="px-2">
                  <EntityRow
                    title={fee.name}
                    subtitle={`${fee.amount}${
                      fee.category ? ` · ${fee.category}` : ""
                    }${
                      fee.duration_minutes
                        ? ` · ${fee.duration_minutes} min`
                        : ""
                    }`}
                    trailing={
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => remove.mutate(fee.id)}
                      >
                        Remove
                      </Button>
                    }
                  />
                </li>
              ))}
            </EntityList>
          )}
        </SectionCard>
      </SettingsSection>

      <ServiceCreateModal
        clinicId={clinicId}
        open={createOpen}
        onOpenChange={setCreateOpen}
      />
    </div>
  );
}
