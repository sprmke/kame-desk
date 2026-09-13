import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { keepPreviousData } from "@tanstack/react-query";
import { ClipboardList, Plus } from "lucide-react";
import { api, type InsuranceClaim } from "@/lib/apiClient";
import { useSession } from "@/hooks/useSession";
import { useListSearch } from "@/hooks/useListSearch";
import { SectionHeaderActions } from "@/components/layout/SectionHeaderActions";
import { Money } from "@/components/Money";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
import { EmptyState } from "@/components/EmptyState";
import { ClaimsListSkeleton } from "@/components/skeletons/PageSkeletons";
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
import { ClaimCreateModal } from "@/features/billing/components/ClaimCreateModal";
import {
  PayerTypeSelect,
  RowStatusSelect,
} from "@/features/billing/components/PayerFormFields";

const STATUSES = ["draft", "submitted", "approved", "denied", "paid"] as const;
const CLAIM_VIEWS: ListViewMode[] = ["table", "list"];
const CLAIM_EXTRA = ["status", "payerType"] as const;
const CLAIM_SORTS = [
  { value: "created_at:desc", label: "Newest" },
  { value: "created_at:asc", label: "Oldest" },
  { value: "amount:desc", label: "Amount high" },
  { value: "status:asc", label: "Status" },
  { value: "patient:asc", label: "Patient" },
] as const;

function claimSubtitle(claim: InsuranceClaim) {
  return `${claim.provider} (${claim.payer_type}) · PHP ${claim.amount}${
    claim.invoice_number ? ` · ${claim.invoice_number}` : ""
  }`;
}

export function ClaimsListPage() {
  const qc = useQueryClient();
  const { can } = useSession();
  const canWrite = can("billing:write");
  const [createOpen, setCreateOpen] = useState(false);
  const list = useListSearch({
    defaultSort: "created_at:desc",
    views: CLAIM_VIEWS,
    extraKeys: CLAIM_EXTRA,
  });
  const status = list.extras.status;
  const payerType = list.extras.payerType;

  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: [
      "claims",
      status,
      payerType,
      list.q,
      list.page,
      list.limit,
      list.sort,
    ],
    queryFn: () =>
      api.listClaims({
        status: status || undefined,
        payer_type: payerType || undefined,
        q: list.q || undefined,
        page: list.page,
        page_size: list.limit,
        sort: list.sort,
      }),
    placeholderData: keepPreviousData,
  });

  const patch = useMutation({
    mutationFn: (args: { id: string; status: string }) =>
      api.patchClaim(args.id, { status: args.status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["claims"] }),
  });

  const requestLoa = useMutation({
    mutationFn: (args: {
      claimId: string;
      patientId: string;
      hmoName: string;
    }) =>
      api.createLoaRequest({
        patient_id: args.patientId,
        hmo_name: args.hmoName,
        claim_id: args.claimId,
      }),
    onSuccess: async (loa) => {
      await qc.invalidateQueries({ queryKey: ["loa-requests"] });
      if (loa.claim_id) {
        await api.patchClaim(loa.claim_id, { loa_request_id: loa.id });
      }
      qc.invalidateQueries({ queryKey: ["claims"] });
    },
  });

  function loaControl(claim: InsuranceClaim) {
    if (claim.loa_request_id) {
      return <span className="text-sm text-muted-foreground">Linked</span>;
    }
    if (!canWrite || claim.payer_type !== "hmo") {
      return <span className="text-sm text-muted-foreground">—</span>;
    }
    return (
      <Button
        type="button"
        variant="ghost"
        size="sm"
        disabled={requestLoa.isPending}
        onClick={() =>
          requestLoa.mutate({
            claimId: claim.id,
            patientId: claim.patient_id,
            hmoName: claim.provider,
          })
        }
      >
        Request LOA
      </Button>
    );
  }

  function statusControl(claim: InsuranceClaim) {
    return (
      <RowStatusSelect
        value={claim.status}
        options={STATUSES}
        ariaLabel={`Status for ${claim.provider}`}
        disabled={!canWrite}
        onChange={(value) => patch.mutate({ id: claim.id, status: value })}
      />
    );
  }

  const items = data?.items ?? [];
  const filtered = Boolean(list.q || status || payerType);

  return (
    <div className="flex flex-col gap-4">
      {canWrite ? (
        <SectionHeaderActions>
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" />
            New claim
          </Button>
        </SectionHeaderActions>
      ) : null}

      <ManagedList
        entityLabel="claims"
        total={data?.total ?? 0}
        page={list.page}
        limit={list.limit}
        view={list.view}
        views={CLAIM_VIEWS}
        onViewChange={list.setView}
        onPageChange={list.setPage}
        onLimitChange={list.setLimit}
        sort={list.sort}
        sortOptions={CLAIM_SORTS}
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
        refine={
          <Field>
            <FieldLabel htmlFor="claim-payer-filter" label="Payer type" />
            <PayerTypeSelect
              id="claim-payer-filter"
              value={payerType}
              onChange={(value) =>
                list.setParams({ payerType: value, page: 1 })
              }
              allowEmpty
            />
          </Field>
        }
        refineCount={(status ? 1 : 0) + (payerType ? 1 : 0)}
        onClearFilters={() =>
          list.setParams({ status: undefined, payerType: undefined, page: 1 })
        }
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        onRetry={() => refetch()}
        hideTableView={list.hideTableView}
        empty={
          <EmptyState
            icon={ClipboardList}
            heading={filtered ? "No claims found" : "No claims yet"}
            action={
              !filtered && canWrite ? (
                <Button type="button" onClick={() => setCreateOpen(true)}>
                  New claim
                </Button>
              ) : undefined
            }
          />
        }
      >
        {isLoading ? (
          <ListTableShell>
            <ClaimsListSkeleton />
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
                  <TableHead>Payer</TableHead>
                  <TableHead>
                    <ListSortHeader
                      label="Amount"
                      column="amount"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>LOA</TableHead>
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
                {items.map((claim) => (
                  <TableRow key={claim.id}>
                    <TableCell className="font-medium">
                      {claim.patient_name ?? "Patient"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {claim.provider} ({claim.payer_type})
                    </TableCell>
                    <TableCell>
                      <Money amount={claim.amount} />
                    </TableCell>
                    <TableCell>{loaControl(claim)}</TableCell>
                    <TableCell>{statusControl(claim)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ListTableShell>
        ) : (
          <ListStack>
            {items.map((claim) => (
              <li key={claim.id} className="px-5">
                <EntityRow
                  title={claim.patient_name ?? "Patient"}
                  subtitle={claimSubtitle(claim)}
                  meta={claim.loa_request_id ? "LOA linked" : undefined}
                  trailing={
                    <div className="flex items-center gap-2">
                      {claim.loa_request_id ? null : loaControl(claim)}
                      {statusControl(claim)}
                    </div>
                  }
                />
              </li>
            ))}
          </ListStack>
        )}
      </ManagedList>

      <ClaimCreateModal open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}

export function ClaimsPage() {
  return <ClaimsListPage />;
}
