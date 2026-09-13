import { Link, useNavigate } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { UserPlus, Users } from "lucide-react";
import { api } from "@/lib/apiClient";
import { useSession } from "@/hooks/useSession";
import { useListSearch } from "@/hooks/useListSearch";
import { SectionHeaderActions } from "@/components/layout/SectionHeaderActions";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/EmptyState";
import { PatientListSkeleton } from "@/components/skeletons/PageSkeletons";
import {
  ListSortHeader,
  ListStack,
  ListTableShell,
  ManagedList,
} from "@/components/list";
import { PatientImportModal } from "@/features/patients/components/PatientImportModal";
import { PersonIdentity } from "@/components/PersonIdentity";
import { patientDisambiguator } from "@/features/patients/lib/patientIdentity";
import type { ListViewMode } from "@/lib/list/viewMode";

const PATIENT_VIEWS: ListViewMode[] = ["table", "list"];
const PATIENT_SORTS = [
  { value: "name:asc", label: "Name A-Z" },
  { value: "name:desc", label: "Name Z-A" },
  { value: "number:asc", label: "Number" },
  { value: "created_at:desc", label: "Newest" },
  { value: "created_at:asc", label: "Oldest" },
] as const;

export function PatientListPage() {
  const navigate = useNavigate();
  const list = useListSearch({
    defaultSort: "name:asc",
    views: PATIENT_VIEWS,
  });

  const { can } = useSession();
  const canImport = can("patients:merge");

  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: ["patients", list.q, list.page, list.limit, list.sort],
    queryFn: () =>
      api.listPatients({
        q: list.q || undefined,
        page: list.page,
        page_size: list.limit,
        sort: list.sort,
      }),
    placeholderData: keepPreviousData,
  });

  const patients = data?.items ?? [];
  const total = data?.total ?? 0;

  function openPatient(patientId: string) {
    void navigate({
      to: "/dashboard/patients/$patientId",
      params: { patientId },
    });
  }

  return (
    <div>
      <SectionHeaderActions>
        {canImport ? <PatientImportModal /> : null}
        <Button asChild>
          <Link to="/dashboard/patients/new">
            <UserPlus className="size-4" />
            New patient
          </Link>
        </Button>
      </SectionHeaderActions>

      <ManagedList
        entityLabel="patients"
        total={total}
        page={list.page}
        limit={list.limit}
        view={list.view}
        views={PATIENT_VIEWS}
        onViewChange={list.setView}
        onPageChange={list.setPage}
        onLimitChange={list.setLimit}
        sort={list.sort}
        sortOptions={PATIENT_SORTS}
        onSortChange={list.setSort}
        searchPlaceholder="Search name, contact, ID"
        searchValue={list.q}
        onSearchChange={list.setQuery}
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        onRetry={() => refetch()}
        hideTableView={list.hideTableView}
        empty={
          <EmptyState
            icon={Users}
            heading={list.q ? "No patients found" : "No patients yet"}
            action={
              !list.q ? (
                <Button asChild>
                  <Link to="/dashboard/patients/new">New patient</Link>
                </Button>
              ) : undefined
            }
          />
        }
      >
        {isLoading ? (
          <ListTableShell>
            <PatientListSkeleton />
          </ListTableShell>
        ) : list.view === "list" ? (
          <ListStack>
            {patients.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  className="flex w-full min-h-[44px] cursor-pointer items-center gap-3 px-5 py-3 text-left native-press hover:bg-muted/40"
                  onClick={() => openPatient(p.id)}
                >
                  <PersonIdentity
                    name={p.full_name}
                    patientNumber={String(p.patient_number)}
                    detail={patientDisambiguator(p)}
                  />
                </button>
              </li>
            ))}
          </ListStack>
        ) : (
          <ListTableShell>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <ListSortHeader
                      label="Name"
                      column="name"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>
                    <ListSortHeader
                      label="Patient #"
                      column="number"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
                  <TableHead>Age / sex</TableHead>
                  <TableHead>Contact</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {patients.map((p) => (
                  <TableRow
                    key={p.id}
                    className="cursor-pointer native-press"
                    onClick={() => openPatient(p.id)}
                  >
                    <TableCell>
                      <PersonIdentity name={p.full_name} />
                    </TableCell>
                    <TableCell className="dd-nums text-muted-foreground">
                      #{p.patient_number}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {patientDisambiguator({
                        birthdate: p.birthdate,
                        sex: p.sex,
                        contact_number: null,
                      }) ?? "-"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {p.contact_number ?? "No contact"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ListTableShell>
        )}
      </ManagedList>
    </div>
  );
}
