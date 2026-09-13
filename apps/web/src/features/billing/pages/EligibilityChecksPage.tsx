import { useState } from "react";
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Plus, ShieldCheck } from "lucide-react";
import { api, type EligibilityCheck } from "@/lib/apiClient";
import { useSession } from "@/hooks/useSession";
import { useListSearch } from "@/hooks/useListSearch";
import { SectionHeaderActions } from "@/components/layout/SectionHeaderActions";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
import { EmptyState } from "@/components/EmptyState";
import { EligibilityListSkeleton } from "@/components/skeletons/PageSkeletons";
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
import { EligibilityCreateModal } from "@/features/billing/components/EligibilityCreateModal";
import {
  PayerTypeSelect,
  RowStatusSelect,
} from "@/features/billing/components/PayerFormFields";

const STATUSES = ["pending", "verified", "denied", "expired"] as const;
const VIEWS: ListViewMode[] = ["table", "list"];
const EXTRA_KEYS = ["status", "payerType"] as const;
const SORTS = [
  { value: "checked_at:desc", label: "Newest" },
  { value: "checked_at:asc", label: "Oldest" },
  { value: "status:asc", label: "Status" },
  { value: "payer:asc", label: "Payer" },
  { value: "patient:asc", label: "Patient" },
] as const;

function checkSubtitle(check: EligibilityCheck) {
  return `${check.payer_name} (${check.payer_type})${
    check.member_id ? ` · ${check.member_id}` : ""
  }${check.verified_amount ? ` · PHP ${check.verified_amount}` : ""}`;
}

export function EligibilityChecksPage() {
  const qc = useQueryClient();
  const { can } = useSession();
  const canWrite = can("billing:write");
  const [createOpen, setCreateOpen] = useState(false);
  const list = useListSearch({
    defaultSort: "checked_at:desc",
    views: VIEWS,
    extraKeys: EXTRA_KEYS,
  });
  const status = list.extras.status;
  const payerType = list.extras.payerType;

  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: [
      "eligibility-checks",
      status,
      payerType,
      list.q,
      list.page,
      list.limit,
      list.sort,
    ],
    queryFn: () =>
      api.listEligibilityChecks({
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
      api.patchEligibilityCheck(args.id, {
        status: args.status as EligibilityCheck["status"],
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["eligibility-checks"] }),
  });

  function statusControl(check: EligibilityCheck) {
    return (
      <RowStatusSelect
        value={check.status}
        options={STATUSES}
        ariaLabel={`Status for ${check.payer_name}`}
        disabled={!canWrite}
        onChange={(value) => patch.mutate({ id: check.id, status: value })}
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
            New check
          </Button>
        </SectionHeaderActions>
      ) : null}

      <ManagedList
        entityLabel="checks"
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
        refine={
          <Field>
            <FieldLabel htmlFor="eligibility-payer-filter" label="Payer type" />
            <PayerTypeSelect
              id="eligibility-payer-filter"
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
            icon={ShieldCheck}
            heading={filtered ? "No checks found" : "No eligibility checks yet"}
            action={
              !filtered && canWrite ? (
                <Button type="button" onClick={() => setCreateOpen(true)}>
                  New check
                </Button>
              ) : undefined
            }
          />
        }
      >
        {isLoading ? (
          <ListTableShell>
            <EligibilityListSkeleton />
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
                  <TableHead>Member ID</TableHead>
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
                {items.map((check) => (
                  <TableRow key={check.id}>
                    <TableCell className="font-medium">
                      {check.patient_name ?? "Patient"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {check.payer_name} ({check.payer_type})
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {check.member_id ?? "—"}
                    </TableCell>
                    <TableCell>{statusControl(check)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ListTableShell>
        ) : (
          <ListStack>
            {items.map((check) => (
              <li key={check.id} className="px-5">
                <EntityRow
                  title={check.patient_name ?? "Patient"}
                  subtitle={checkSubtitle(check)}
                  trailing={statusControl(check)}
                />
              </li>
            ))}
          </ListStack>
        )}
      </ManagedList>

      <EligibilityCreateModal open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
