import { useMemo } from "react";
import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { api } from "@/lib/apiClient";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { Badge } from "@/components/ui/badge";
import { EntityRow } from "@/components/ui/entity-row";
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

const TENANT_VIEWS: ListViewMode[] = ["table", "list"];
const TENANT_SORTS = [
  { value: "name:asc", label: "Name A-Z" },
  { value: "name:desc", label: "Name Z-A" },
  { value: "status:asc", label: "Status" },
] as const;

export function PlatformTenantsPage() {
  const list = useListSearch({
    defaultSort: "name:asc",
    views: TENANT_VIEWS,
  });
  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: ["platform-tenants"],
    queryFn: () => api.listPlatformTenants(),
  });

  const filtered = useMemo(() => {
    let rows = data ?? [];
    if (list.q) {
      const q = list.q.toLowerCase();
      rows = rows.filter(
        (row) =>
          row.name.toLowerCase().includes(q) ||
          row.status.toLowerCase().includes(q) ||
          row.plan_key.toLowerCase().includes(q),
      );
    }
    const [key, dir] = list.sort.split(":");
    const factor = dir === "desc" ? -1 : 1;
    return [...rows].sort((a, b) => {
      if (key === "status") return a.status.localeCompare(b.status) * factor;
      return a.name.localeCompare(b.name) * factor;
    });
  }, [data, list.q, list.sort]);

  const total = filtered.length;
  const items = filtered.slice(
    (list.page - 1) * list.limit,
    list.page * list.limit,
  );

  return (
    <div className={pageContainerClass()}>
      <PageHeader title="Tenants" />
      <ManagedList
        entityLabel="organizations"
        total={total}
        page={list.page}
        limit={list.limit}
        view={list.view}
        views={TENANT_VIEWS}
        onViewChange={list.setView}
        onPageChange={list.setPage}
        onLimitChange={list.setLimit}
        sort={list.sort}
        sortOptions={TENANT_SORTS}
        onSortChange={list.setSort}
        searchPlaceholder="Search clinics"
        searchValue={list.q}
        onSearchChange={list.setQuery}
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        onRetry={() => refetch()}
        hideTableView={list.hideTableView}
        empty={<EmptyState icon={Building2} heading="No organizations" />}
      >
        {isLoading ? (
          <ListTableShell>
            <div className="h-40 animate-pulse bg-muted" />
          </ListTableShell>
        ) : list.view === "table" ? (
          <ListTableShell>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Organization</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Clinics</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((row) => (
                  <TableRow
                    key={row.id}
                    className="cursor-pointer native-press"
                  >
                    <TableCell>
                      <Link
                        to="/platform/tenants/$clinicId"
                        params={{ clinicId: row.id }}
                        className="font-medium text-foreground"
                      >
                        {row.name}
                      </Link>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {row.plan_key}
                    </TableCell>
                    <TableCell>{row.clinic_count ?? 1}</TableCell>
                    <TableCell>{row.status}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ListTableShell>
        ) : (
          <ListStack>
            {items.map((row) => (
              <li key={row.id}>
                <Link
                  to="/platform/tenants/$clinicId"
                  params={{ clinicId: row.id }}
                  className="block cursor-pointer px-5 native-press hover:bg-muted/40"
                >
                  <EntityRow
                    title={row.name}
                    subtitle={`${row.status} · ${row.plan_key}`}
                  />
                </Link>
              </li>
            ))}
          </ListStack>
        )}
      </ManagedList>
    </div>
  );
}
