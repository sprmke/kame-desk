import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { useListSearch } from "@/hooks/useListSearch";
import { DateRangePicker } from "@/components/ui/date-picker";
import { AuditLogSkeleton } from "@/components/skeletons/PageSkeletons";
import { EmptyState } from "@/components/EmptyState";
import { Label } from "@/components/ui/label";
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
import { EntityRow } from "@/components/ui/entity-row";

const ACTOR_TYPES = ["user", "system", "ai_assistant"] as const;
const ACTIONS = [
  "patient.created",
  "patient.merged",
  "appointment.created",
  "invoice.payment_recorded",
  "invoice.credit_issued",
  "invoice.voided",
  "clinical_order.created",
  "reminder.retried",
  "insurance_claim.created",
  "insurance_claim.updated",
] as const;
const TARGET_TYPES = [
  "patient",
  "appointment",
  "invoice",
  "clinical_order",
  "reminder",
  "insurance_claim",
  "generated_document",
] as const;

const AUDIT_VIEWS: ListViewMode[] = ["table", "list"];
const AUDIT_EXTRA = [
  "actorType",
  "action",
  "targetType",
  "from",
  "to",
] as const;
const AUDIT_SORTS = [
  { value: "created_at:desc", label: "Newest" },
  { value: "created_at:asc", label: "Oldest" },
] as const;

export function AuditLogPage() {
  const clinicId = getClinicId();
  const list = useListSearch({
    defaultSort: "created_at:desc",
    views: AUDIT_VIEWS,
    extraKeys: AUDIT_EXTRA,
  });
  const actorType = list.extras.actorType;
  const action = list.extras.action;
  const targetType = list.extras.targetType;
  const fromDate = list.extras.from;
  const toDate = list.extras.to;

  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: [
      "activity-log",
      clinicId,
      list.page,
      list.limit,
      list.q,
      list.sort,
      actorType,
      action,
      targetType,
      fromDate,
      toDate,
    ],
    queryFn: () =>
      api.listActivityLog(clinicId!, {
        page: list.page,
        page_size: list.limit,
        q: list.q || undefined,
        sort: list.sort,
        actor_type: actorType || undefined,
        action: action || undefined,
        target_type: targetType || undefined,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
      }),
    enabled: Boolean(clinicId),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const refineCount =
    (actorType ? 1 : 0) +
    (action ? 1 : 0) +
    (targetType ? 1 : 0) +
    (fromDate || toDate ? 1 : 0);

  return (
    <div>
      <ManagedList
        entityLabel="entries"
        total={total}
        page={list.page}
        limit={list.limit}
        view={list.view}
        views={AUDIT_VIEWS}
        onViewChange={list.setView}
        onPageChange={list.setPage}
        onLimitChange={list.setLimit}
        sort={list.sort}
        sortOptions={AUDIT_SORTS}
        onSortChange={list.setSort}
        searchPlaceholder="Search action"
        searchValue={list.q}
        onSearchChange={list.setQuery}
        leading={
          <Select
            value={actorType || "all"}
            onValueChange={(value) =>
              list.setParams({ actorType: value, page: 1 })
            }
          >
            <SelectTrigger
              className="h-10 min-h-[44px] w-full min-w-[9rem] lg:min-h-10"
              aria-label="Actor"
            >
              <SelectValue placeholder="Actor" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All actors</SelectItem>
              {ACTOR_TYPES.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
        refine={
          <>
            <div className="flex flex-col gap-1.5">
              <Label>Action</Label>
              <Select
                value={action || "all"}
                onValueChange={(value) =>
                  list.setParams({ action: value, page: 1 })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All actions</SelectItem>
                  {ACTIONS.map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Target</Label>
              <Select
                value={targetType || "all"}
                onValueChange={(value) =>
                  list.setParams({ targetType: value, page: 1 })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All targets</SelectItem>
                  {TARGET_TYPES.map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="audit-date-range">Date range</Label>
              <DateRangePicker
                id="audit-date-range"
                from={fromDate}
                to={toDate}
                onValueChange={(range) => list.setParams({ ...range, page: 1 })}
              />
            </div>
          </>
        }
        refineCount={refineCount}
        onClearFilters={() =>
          list.setParams({
            actorType: undefined,
            action: undefined,
            targetType: undefined,
            from: undefined,
            to: undefined,
            page: 1,
          })
        }
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        onRetry={() => refetch()}
        hideTableView={list.hideTableView}
        empty={
          <EmptyState
            icon={History}
            heading={
              list.q || actorType || action || targetType || fromDate || toDate
                ? "No matching entries"
                : "No activity yet"
            }
            description="Use filters or search to find specific actions, actors, or targets."
          />
        }
      >
        {isLoading ? (
          <ListTableShell>
            <AuditLogSkeleton />
          </ListTableShell>
        ) : list.view === "table" ? (
          <ListTableShell>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <ListSortHeader
                      label="When"
                      column="created_at"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>Summary</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Actor</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="text-muted-foreground">
                      {new Date(row.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="font-medium text-foreground">
                      {row.summary}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {row.action}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {row.actor_name ?? row.actor_type}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ListTableShell>
        ) : (
          <ListStack>
            {items.map((row) => (
              <li key={row.id} className="px-5">
                <EntityRow
                  title={row.summary}
                  subtitle={`${row.action} · ${row.actor_name ?? row.actor_type}`}
                  meta={new Date(row.created_at).toLocaleString()}
                />
              </li>
            ))}
          </ListStack>
        )}
      </ManagedList>
    </div>
  );
}
