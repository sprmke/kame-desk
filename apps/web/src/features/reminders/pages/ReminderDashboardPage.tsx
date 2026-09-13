import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { api } from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/EmptyState";
import { ReminderListSkeleton } from "@/components/skeletons/PageSkeletons";
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
import { useListSearch } from "@/hooks/useListSearch";
import { ListStack, ListTableShell, ManagedList } from "@/components/list";
import type { ListViewMode } from "@/lib/list/viewMode";

const STATUS_VARIANT: Record<
  string,
  "default" | "brand" | "success" | "warning" | "error" | "info"
> = {
  pending: "warning",
  sent: "success",
  failed: "error",
  cancelled: "default",
};

const REMINDER_VIEWS: ListViewMode[] = ["table", "list"];
const REMINDER_EXTRA = ["status"] as const;
const REMINDER_SORTS = [
  { value: "scheduled:asc", label: "Soonest send" },
  { value: "scheduled:desc", label: "Latest send" },
  { value: "status:asc", label: "Status" },
] as const;

export function ReminderDashboardPage() {
  const qc = useQueryClient();
  const list = useListSearch({
    defaultSort: "scheduled:asc",
    views: REMINDER_VIEWS,
    extraKeys: REMINDER_EXTRA,
  });
  const status = list.extras.status || "all";
  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: [
      "reminders",
      "search",
      status,
      list.q,
      list.page,
      list.limit,
      list.sort,
    ],
    queryFn: () =>
      api.searchReminders({
        status: status !== "all" ? status : undefined,
        q: list.q || undefined,
        page: list.page,
        page_size: list.limit,
        sort: list.sort,
      }),
    placeholderData: keepPreviousData,
  });
  const retry = useMutation({
    mutationFn: (id: string) => api.retryReminder(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  });

  const total = data?.total ?? 0;
  const items = data?.items ?? [];

  return (
    <div>
      <ManagedList
        entityLabel="reminders"
        total={total}
        page={list.page}
        limit={list.limit}
        view={list.view}
        views={REMINDER_VIEWS}
        onViewChange={list.setView}
        onPageChange={list.setPage}
        onLimitChange={list.setLimit}
        sort={list.sort}
        sortOptions={REMINDER_SORTS}
        onSortChange={list.setSort}
        searchPlaceholder="Search patient or channel"
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
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="sent">Sent</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        }
        refineCount={status !== "all" ? 1 : 0}
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        onRetry={() => refetch()}
        hideTableView={list.hideTableView}
        empty={
          <EmptyState
            icon={Bell}
            heading={
              status !== "all" || list.q
                ? "No reminders found"
                : "No reminders yet"
            }
            description="Reminders for appointments, follow-ups, and recalls will appear here."
          />
        }
      >
        {isLoading ? (
          <ListTableShell>
            <ReminderListSkeleton />
          </ListTableShell>
        ) : list.view === "table" ? (
          <ListTableShell>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Channel</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="font-medium">
                      {row.patient_name ?? "Patient"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {row.reminder_type}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {row.channel}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={STATUS_VARIANT[row.status] ?? "default"}
                        dot
                      >
                        {row.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {row.status === "failed" ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={retry.isPending}
                          onClick={() => retry.mutate(row.id)}
                        >
                          Retry
                        </Button>
                      ) : null}
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
                  title={row.patient_name ?? "Patient"}
                  subtitle={`${row.reminder_type} · ${row.channel}`}
                  trailing={
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={STATUS_VARIANT[row.status] ?? "default"}
                        dot
                      >
                        {row.status}
                      </Badge>
                      {row.status === "failed" ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={retry.isPending}
                          onClick={() => retry.mutate(row.id)}
                        >
                          Retry
                        </Button>
                      ) : null}
                    </div>
                  }
                />
              </li>
            ))}
          </ListStack>
        )}
      </ManagedList>
    </div>
  );
}
