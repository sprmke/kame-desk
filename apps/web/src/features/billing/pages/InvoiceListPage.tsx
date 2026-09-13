import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { FileText, TriangleAlert } from "lucide-react";
import { api, type BirCompliance, type Invoice } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { useListSearch } from "@/hooks/useListSearch";
import { SectionHeaderActions } from "@/components/layout/SectionHeaderActions";
import { Money } from "@/components/Money";
import { PaymentStatus } from "@/components/StatusIndicator";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { InvoiceListSkeleton } from "@/components/skeletons/PageSkeletons";
import { EntityRow } from "@/components/ui/entity-row";
import { DateRangePicker } from "@/components/ui/date-picker";
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

function birComplianceWarning(bir: BirCompliance | undefined): string | null {
  if (!bir) return null;
  if (!bir.tin)
    return "Add your clinic's TIN in Settings so receipts satisfy BIR filing.";
  if (
    bir.compliance_mode !== "not_yet_accredited" &&
    !bir.accreditation_number
  ) {
    return "Add your PTU/CAS accreditation number in Settings.";
  }
  if (bir.accreditation_valid_until) {
    const today = new Date().toISOString().slice(0, 10);
    if (bir.accreditation_valid_until < today) {
      return "Your PTU/CAS accreditation has expired. Update it in Settings.";
    }
  }
  return null;
}

const INVOICE_VIEWS: ListViewMode[] = ["table", "list"];
const INVOICE_EXTRA = ["status", "from", "to"] as const;
const INVOICE_SORTS = [
  { value: "created_at:desc", label: "Newest" },
  { value: "created_at:asc", label: "Oldest" },
  { value: "total:desc", label: "Amount high" },
  { value: "total:asc", label: "Amount low" },
  { value: "status:asc", label: "Status" },
] as const;

function invoiceSubtitle(inv: Invoice) {
  return `${inv.patient_name ?? "Patient"} · PHP ${inv.total}${
    Number(inv.balance_due) > 0 ? ` · due ${inv.balance_due}` : ""
  }${
    Number(inv.amount_credited ?? 0) > 0
      ? ` · credited ${inv.amount_credited}`
      : ""
  }`;
}

export function InvoiceListPage() {
  const clinicId = getClinicId();
  const list = useListSearch({
    defaultSort: "created_at:desc",
    views: INVOICE_VIEWS,
    extraKeys: INVOICE_EXTRA,
  });
  const status = list.extras.status || "all";
  const fromDate = list.extras.from;
  const toDate = list.extras.to;

  const { data, isLoading, isFetching, isError, refetch } = useQuery({
    queryKey: [
      "clinic-invoices",
      list.q,
      status,
      fromDate,
      toDate,
      list.page,
      list.limit,
      list.sort,
    ],
    queryFn: () =>
      api.listClinicInvoices({
        q: list.q || undefined,
        status: status !== "all" ? status : undefined,
        start_from: fromDate
          ? new Date(`${fromDate}T00:00:00+08:00`).toISOString()
          : undefined,
        start_to: toDate
          ? new Date(`${toDate}T23:59:59+08:00`).toISOString()
          : undefined,
        page: list.page,
        page_size: list.limit,
        sort: list.sort,
      }),
  });

  const { data: outstanding } = useQuery({
    queryKey: ["outstanding", clinicId],
    queryFn: () => api.getOutstandingBalances(clinicId!),
    enabled: Boolean(clinicId),
  });

  const { data: clinic } = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => api.getClinic(clinicId!),
    enabled: Boolean(clinicId),
  });
  const complianceWarning = birComplianceWarning(
    clinic?.bir_compliance ?? undefined,
  );

  async function exportCsv() {
    const csv = await api.exportClinicInvoicesCsv({
      q: list.q || undefined,
      status: status !== "all" ? status : undefined,
    });
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "invoices.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const filtered = Boolean(list.q || status !== "all" || fromDate || toDate);

  return (
    <div className="flex flex-col gap-4">
      <SectionHeaderActions>
        <Button
          type="button"
          variant="outline"
          onClick={() => void exportCsv()}
        >
          Export
        </Button>
      </SectionHeaderActions>

      {complianceWarning && (
        <p className="mb-4 flex items-start gap-2 text-sm text-foreground">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          {complianceWarning}
        </p>
      )}

      {outstanding && Number(outstanding.total_outstanding) > 0 && (
        <p className="mb-4 text-sm">
          Outstanding: <Money amount={outstanding.total_outstanding} />
        </p>
      )}

      <ManagedList
        entityLabel="invoices"
        total={total}
        page={list.page}
        limit={list.limit}
        view={list.view}
        views={INVOICE_VIEWS}
        onViewChange={list.setView}
        onPageChange={list.setPage}
        onLimitChange={list.setLimit}
        sort={list.sort}
        sortOptions={INVOICE_SORTS}
        onSortChange={list.setSort}
        searchPlaceholder={FORM_PLACEHOLDERS.searchInvoices}
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
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="issued">Issued</SelectItem>
              <SelectItem value="partially_paid">Partial</SelectItem>
              <SelectItem value="paid">Paid</SelectItem>
              <SelectItem value="void">Void</SelectItem>
            </SelectContent>
          </Select>
        }
        refine={
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="invoice-date-range">Date range</Label>
            <DateRangePicker
              id="invoice-date-range"
              from={fromDate}
              to={toDate}
              onValueChange={(range) => list.setParams({ ...range, page: 1 })}
            />
          </div>
        }
        refineCount={(status !== "all" ? 1 : 0) + (fromDate || toDate ? 1 : 0)}
        onClearFilters={() =>
          list.setParams({
            status: undefined,
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
            icon={FileText}
            heading={filtered ? "No invoices found" : "No invoices yet"}
          />
        }
      >
        {isLoading ? (
          <ListTableShell>
            <InvoiceListSkeleton />
          </ListTableShell>
        ) : list.view === "table" ? (
          <ListTableShell>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice</TableHead>
                  <TableHead>Patient</TableHead>
                  <TableHead>
                    <ListSortHeader
                      label="Amount"
                      column="total"
                      sort={list.sort}
                      onSort={list.setSort}
                    />
                  </TableHead>
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
                {items.map((inv) => (
                  <TableRow
                    key={inv.id}
                    className="cursor-pointer native-press"
                  >
                    <TableCell>
                      <Link
                        to="/dashboard/patients/$patientId/invoices/$invoiceId"
                        params={{
                          patientId: inv.patient_id,
                          invoiceId: inv.id,
                        }}
                        className="font-medium text-foreground"
                      >
                        {inv.invoice_number ?? "Draft"}
                      </Link>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {inv.patient_name ?? "Patient"}
                    </TableCell>
                    <TableCell>
                      <Money amount={inv.total} />
                    </TableCell>
                    <TableCell>
                      <PaymentStatus status={inv.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ListTableShell>
        ) : (
          <ListStack>
            {items.map((inv) => (
              <li key={inv.id}>
                <Link
                  to="/dashboard/patients/$patientId/invoices/$invoiceId"
                  params={{
                    patientId: inv.patient_id,
                    invoiceId: inv.id,
                  }}
                  className="block cursor-pointer px-5 native-press hover:bg-muted/40"
                >
                  <EntityRow
                    title={inv.invoice_number ?? "Draft"}
                    subtitle={invoiceSubtitle(inv)}
                    trailing={<PaymentStatus status={inv.status} />}
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
