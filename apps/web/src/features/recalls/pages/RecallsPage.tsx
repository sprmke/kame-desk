import { Link, useNavigate } from "@tanstack/react-router";
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { RotateCcw } from "lucide-react";
import { EmptyState } from "@/components/EmptyState";
import { RecallsSkeleton } from "@/components/skeletons/PageSkeletons";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { useListSearch } from "@/hooks/useListSearch";
import {
  ListSortHeader,
  ListStack,
  ListTableShell,
  ManagedList,
} from "@/components/list";
import type { ListViewMode } from "@/lib/list/viewMode";
import { EntityRow } from "@/components/ui/entity-row";

const RECALL_VIEWS: ListViewMode[] = ["table", "list"];
const RECALL_EXTRA = ["status"] as const;
const RECALL_SORTS = [
  { value: "due_date:asc", label: "Due soonest" },
  { value: "due_date:desc", label: "Due latest" },
  { value: "created_at:desc", label: "Newest" },
] as const;

export function RecallsPage() {
  const clinicId = getClinicId();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const list = useListSearch({
    defaultSort: "due_date:asc",
    views: RECALL_VIEWS,
    extraKeys: RECALL_EXTRA,
  });
  const status = list.extras.status || "pending";

  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: [
      "recalls",
      clinicId,
      status,
      list.q,
      list.page,
      list.limit,
      list.sort,
    ],
    queryFn: () =>
      api.listRecalls(clinicId!, {
        status,
        q: list.q || undefined,
        page: list.page,
        page_size: list.limit,
        sort: list.sort,
      }),
    enabled: Boolean(clinicId),
    placeholderData: keepPreviousData,
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patchRecall(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["recalls", clinicId] });
      qc.invalidateQueries({ queryKey: ["recalls-widget", clinicId] });
    },
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  function actions(row: (typeof items)[number]) {
    return (
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() =>
            navigate({
              to: "/dashboard/appointments/new",
              search: { patientId: row.patient_id },
            })
          }
        >
          Book
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() =>
            updateStatus.mutate({ id: row.id, status: "contacted" })
          }
        >
          Contacted
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() =>
            updateStatus.mutate({ id: row.id, status: "dismissed" })
          }
        >
          Dismiss
        </Button>
      </div>
    );
  }

  return (
    <div>
      <ManagedList
        entityLabel="recalls"
        total={total}
        page={list.page}
        limit={list.limit}
        view={list.view}
        views={RECALL_VIEWS}
        onViewChange={list.setView}
        onPageChange={list.setPage}
        onLimitChange={list.setLimit}
        sort={list.sort}
        sortOptions={RECALL_SORTS}
        onSortChange={list.setSort}
        searchPlaceholder="Search patient or source"
        searchValue={list.q}
        onSearchChange={list.setQuery}
        leading={
          <Select
            value={status}
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
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="contacted">Contacted</SelectItem>
              <SelectItem value="booked">Booked</SelectItem>
              <SelectItem value="dismissed">Dismissed</SelectItem>
            </SelectContent>
          </Select>
        }
        refineCount={status !== "pending" ? 1 : 0}
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        onRetry={() => refetch()}
        hideTableView={list.hideTableView}
        empty={
          <EmptyState
            icon={RotateCcw}
            heading={
              status === "pending" && !list.q
                ? "No pending recalls"
                : "No recalls found"
            }
            description="Follow-up dates from signed SOAP notes and recall rules appear here."
          />
        }
      >
        {isLoading ? (
          <ListTableShell>
            <RecallsSkeleton />
          </ListTableShell>
        ) : list.view === "table" ? (
          <ListTableShell>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient</TableHead>
                  <TableHead>
                    <ListSortHeader
                      label="Due"
                      column="due_date"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="font-medium">
                      {row.patient_name ?? "Patient"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {row.due_date}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {row.source}
                    </TableCell>
                    <TableCell>{actions(row)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ListTableShell>
        ) : (
          <ListStack>
            {items.map((row) => (
              <li
                key={row.id}
                className="flex flex-wrap items-center justify-between gap-3 px-5 py-3"
              >
                <EntityRow
                  title={row.patient_name ?? "Patient"}
                  subtitle={`Due ${row.due_date} · ${row.source}`}
                />
                {actions(row)}
              </li>
            ))}
          </ListStack>
        )}
      </ManagedList>
    </div>
  );
}

export function PendingRecallsWidget() {
  const clinicId = getClinicId();
  const { data } = useQuery({
    queryKey: ["recalls-widget", clinicId],
    queryFn: () => api.listRecalls(clinicId!),
    enabled: Boolean(clinicId),
  });

  const items = data?.items ?? [];
  if (items.length === 0) return null;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="text-base">Pending follow-ups</CardTitle>
        <Link
          to="/dashboard/recalls"
          className="text-sm font-medium text-primary hover:underline"
        >
          View all
        </Link>
      </CardHeader>
      <CardContent className="flex flex-col gap-1 px-3">
        {items.slice(0, 5).map((row) => (
          <div
            key={row.id}
            className="flex justify-between rounded-lg px-2 py-2 text-sm"
          >
            <span className="text-foreground">
              {row.patient_name ?? "Patient"}
            </span>
            <span className="text-muted-foreground">{row.due_date}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
