import { useState } from "react";
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Plus, Stamp } from "lucide-react";
import { api, type LoaRequest } from "@/lib/apiClient";
import { useSession } from "@/hooks/useSession";
import { useListSearch } from "@/hooks/useListSearch";
import { SectionHeaderActions } from "@/components/layout/SectionHeaderActions";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { LoaListSkeleton } from "@/components/skeletons/PageSkeletons";
import { EntityRow } from "@/components/ui/entity-row";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ListSortHeader,
  ListStack,
  ListTableShell,
  ManagedList,
} from "@/components/list";
import type { ListViewMode } from "@/lib/list/viewMode";
import { LoaCreateModal } from "@/features/billing/components/LoaCreateModal";
import { RowStatusSelect } from "@/features/billing/components/PayerFormFields";

const STATUSES = ["requested", "submitted", "approved", "denied"] as const;
const VIEWS: ListViewMode[] = ["table", "list"];
const EXTRA_KEYS = ["status"] as const;
const SORTS = [
  { value: "created_at:desc", label: "Newest" },
  { value: "created_at:asc", label: "Oldest" },
  { value: "status:asc", label: "Status" },
  { value: "payer:asc", label: "Payer" },
  { value: "patient:asc", label: "Patient" },
] as const;

function LoaClaimLinker({
  loaId,
  patientId,
}: {
  loaId: string;
  patientId: string;
}) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const { data: claims } = useQuery({
    queryKey: ["claims", "patient", patientId],
    queryFn: () => api.listClaims({ patient_id: patientId }),
    enabled: open,
  });
  const link = useMutation({
    mutationFn: (claimId: string) =>
      api.patchLoaRequest(loaId, { claim_id: claimId }),
    onSuccess: () => {
      setOpen(false);
      qc.invalidateQueries({ queryKey: ["loa-requests"] });
    },
  });

  if (!open) {
    return (
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setOpen(true)}
      >
        Link claim
      </Button>
    );
  }

  const unlinked = (claims?.items ?? []).filter((c) => !c.loa_request_id);

  return (
    <div className="flex items-center gap-2">
      <Select
        onValueChange={(value) => value && link.mutate(value)}
        disabled={unlinked.length === 0}
      >
        <SelectTrigger size="sm" className="w-48">
          <SelectValue
            placeholder={
              unlinked.length === 0 ? "No open claims" : "Select claim"
            }
          />
        </SelectTrigger>
        <SelectContent>
          {unlinked.map((claim) => (
            <SelectItem key={claim.id} value={claim.id}>
              {claim.provider} · PHP {claim.amount}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setOpen(false)}
      >
        Cancel
      </Button>
    </div>
  );
}

function loaSubtitle(loa: LoaRequest) {
  return `${loa.hmo_name}${
    loa.reference_number ? ` · Ref ${loa.reference_number}` : ""
  }`;
}

export function LoaRequestsPage() {
  const qc = useQueryClient();
  const { can } = useSession();
  const canWrite = can("billing:write");
  const [createOpen, setCreateOpen] = useState(false);
  const list = useListSearch({
    defaultSort: "created_at:desc",
    views: VIEWS,
    extraKeys: EXTRA_KEYS,
  });
  const status = list.extras.status;

  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: [
      "loa-requests",
      status,
      list.q,
      list.page,
      list.limit,
      list.sort,
    ],
    queryFn: () =>
      api.listLoaRequests({
        status: status || undefined,
        q: list.q || undefined,
        page: list.page,
        page_size: list.limit,
        sort: list.sort,
      }),
    placeholderData: keepPreviousData,
  });

  const patch = useMutation({
    mutationFn: (args: { id: string; status: string }) =>
      api.patchLoaRequest(args.id, {
        status: args.status as LoaRequest["status"],
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["loa-requests"] }),
  });

  function statusControl(loa: LoaRequest) {
    return (
      <RowStatusSelect
        value={loa.status}
        options={STATUSES}
        ariaLabel={`Status for LOA to ${loa.hmo_name}`}
        disabled={!canWrite}
        onChange={(value) => patch.mutate({ id: loa.id, status: value })}
      />
    );
  }

  const items = data?.items ?? [];
  const filtered = Boolean(list.q || status);

  return (
    <div className="flex flex-col gap-4">
      {canWrite ? (
        <SectionHeaderActions>
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" />
            New request
          </Button>
        </SectionHeaderActions>
      ) : null}

      <ManagedList
        entityLabel="requests"
        total={data?.total ?? 0}
        page={list.page}
        limit={list.limit}
        view={list.view}
        views={VIEWS}
        onViewChange={list.setView}
        onPageChange={list.setPage}
        onLimitChange={list.setLimit}
        sort={list.sort}
        sortOptions={SORTS}
        onSortChange={list.setSort}
        searchPlaceholder="Search patient or payer"
        searchValue={list.q}
        onSearchChange={list.setQuery}
        leading={
          <Select
            value={status || "all"}
            onValueChange={(value) =>
              list.setParams({ status: value, page: 1 })
            }
          >
            <SelectTrigger
              className="h-10 min-h-[44px] w-full min-w-[9rem] lg:min-h-10"
              aria-label="Status"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              {STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
        refineCount={status ? 1 : 0}
        onClearFilters={() => list.setParams({ status: undefined, page: 1 })}
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        onRetry={() => refetch()}
        hideTableView={list.hideTableView}
        empty={
          <EmptyState
            icon={Stamp}
            heading={filtered ? "No requests found" : "No LOA requests yet"}
            action={
              !filtered && canWrite ? (
                <Button type="button" onClick={() => setCreateOpen(true)}>
                  New request
                </Button>
              ) : undefined
            }
          />
        }
      >
        {isLoading ? (
          <ListTableShell>
            <LoaListSkeleton />
          </ListTableShell>
        ) : list.view === "table" ? (
          <ListTableShell>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <ListSortHeader
                      label="Patient"
                      column="patient"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>
                    <ListSortHeader
                      label="Payer"
                      column="payer"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>Claim</TableHead>
                  <TableHead>
                    <ListSortHeader
                      label="Status"
                      column="status"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((loa) => (
                  <TableRow key={loa.id}>
                    <TableCell className="font-medium">
                      {loa.patient_name ?? "Patient"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {loaSubtitle(loa)}
                    </TableCell>
                    <TableCell>
                      {loa.claim_id ? (
                        <span className="text-muted-foreground">Linked</span>
                      ) : canWrite ? (
                        <LoaClaimLinker
                          loaId={loa.id}
                          patientId={loa.patient_id}
                        />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>{statusControl(loa)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ListTableShell>
        ) : (
          <ListStack>
            {items.map((loa) => (
              <li key={loa.id} className="px-5">
                <EntityRow
                  title={loa.patient_name ?? "Patient"}
                  subtitle={loaSubtitle(loa)}
                  meta={
                    !loa.claim_id && canWrite ? (
                      <LoaClaimLinker
                        loaId={loa.id}
                        patientId={loa.patient_id}
                      />
                    ) : undefined
                  }
                  trailing={statusControl(loa)}
                />
              </li>
            ))}
          </ListStack>
        )}
      </ManagedList>

      <LoaCreateModal open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
