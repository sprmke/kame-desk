import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Wallet } from "lucide-react";
import { api } from "@/lib/apiClient";
import { useSession } from "@/hooks/useSession";
import { PageHeader } from "@/components/layout/PageHeader";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { PayersListSkeleton } from "@/components/skeletons/PageSkeletons";
import { EntityList, EntityRow } from "@/components/ui/entity-row";
import { PAYER_TYPES } from "@/features/billing/components/PayerFormFields";
import { PayerCreateModal } from "@/features/settings/payers/components/PayerCreateModal";

function payerTypeLabel(value: string) {
  return PAYER_TYPES.find((type) => type.value === value)?.label ?? value;
}

export function PayersSettingsPage() {
  const qc = useQueryClient();
  const { can } = useSession();
  const canWrite = can("billing:write");
  const [createOpen, setCreateOpen] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["payers"],
    queryFn: () => api.listPayers(),
  });

  const toggleActive = useMutation({
    mutationFn: (args: { id: string; is_active: boolean }) =>
      api.updatePayer(args.id, { is_active: args.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payers"] }),
  });

  const payers = data ?? [];

  return (
    <div>
      <PageHeader
        title="Payers"
        actions={
          canWrite ? (
            <Button type="button" onClick={() => setCreateOpen(true)}>
              <Plus className="size-4" />
              New payer
            </Button>
          ) : undefined
        }
      />
      <SettingsSection divided={false}>
        <SectionCard>
          {isLoading ? (
            <PayersListSkeleton />
          ) : isError ? (
            <ErrorState onRetry={() => refetch()} />
          ) : payers.length === 0 ? (
            <EmptyState
              icon={Wallet}
              heading="No payers yet"
              size="sm"
              action={
                canWrite ? (
                  <Button type="button" onClick={() => setCreateOpen(true)}>
                    New payer
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <EntityList>
              {payers.map((payer) => (
                <li key={payer.id} className="px-2">
                  <EntityRow
                    title={
                      <span
                        className={
                          payer.is_active
                            ? undefined
                            : "text-muted-foreground line-through"
                        }
                      >
                        {payer.name}
                      </span>
                    }
                    subtitle={payerTypeLabel(payer.payer_type)}
                    trailing={
                      canWrite ? (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            toggleActive.mutate({
                              id: payer.id,
                              is_active: !payer.is_active,
                            })
                          }
                        >
                          {payer.is_active ? "Deactivate" : "Reactivate"}
                        </Button>
                      ) : undefined
                    }
                  />
                </li>
              ))}
            </EntityList>
          )}
        </SectionCard>
      </SettingsSection>

      <PayerCreateModal open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
