import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

/* -------------------------------------------------------------------------- */
/* Shared primitives                                                          */
/* -------------------------------------------------------------------------- */

/** Screen-reader text so a skeleton page is not announced as empty. */
function LoadingLabel({ label = "Loading" }: { label?: string }) {
  return (
    <span className="sr-only" role="status">
      {label}
    </span>
  );
}

/** Mirrors `PersonIdentity`: 32px avatar plus name and secondary line. */
function IdentityRowSkeleton({ secondary = true }: { secondary?: boolean }) {
  return (
    <div className="flex min-w-0 items-center gap-2">
      <Skeleton className="size-8 shrink-0 rounded-full" />
      <div className="min-w-0 flex-1">
        <Skeleton className="h-4 w-40 max-w-full" />
        {secondary ? <Skeleton className="mt-1.5 h-3 w-28 max-w-full" /> : null}
      </div>
    </div>
  );
}

/**
 * Mirrors a `Table` body. `widths` are Tailwind width classes for each cell,
 * in column order, so the skeleton keeps the loaded table's column rhythm.
 */
export function TableRowsSkeleton({
  widths,
  rows = 6,
  identityFirstColumn = false,
}: {
  widths: string[];
  rows?: number;
  identityFirstColumn?: boolean;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {widths.map((_, index) => (
            <TableHead key={index}>
              <Skeleton className="h-3 w-16 max-w-full" />
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <TableRow key={rowIndex} className="h-11">
            {widths.map((width, columnIndex) => (
              <TableCell key={columnIndex}>
                {identityFirstColumn && columnIndex === 0 ? (
                  <div className="flex min-w-0 items-center gap-2">
                    <Skeleton className="size-8 shrink-0 rounded-full" />
                    <Skeleton className="h-4 w-32 max-w-full" />
                  </div>
                ) : (
                  <Skeleton className={`h-4 ${width} max-w-full`} />
                )}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/** Mirrors `ListStack` rows built from `EntityRow` with a trailing control. */
export function EntityRowsSkeleton({
  count = 5,
  trailing = true,
  meta = false,
}: {
  count?: number;
  trailing?: boolean;
  meta?: boolean;
}) {
  return (
    <ul className="flex flex-col divide-y divide-border">
      {Array.from({ length: count }).map((_, index) => (
        <li key={index} className="px-5">
          <div className="flex min-h-11 items-center justify-between gap-3 py-3">
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-44 max-w-full" />
              <Skeleton className="mt-1.5 h-3.5 w-64 max-w-full" />
              {meta ? (
                <Skeleton className="mt-1.5 h-3 w-32 max-w-full" />
              ) : null}
            </div>
            {trailing ? (
              <Skeleton className="h-5 w-16 shrink-0 rounded-full" />
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Mirrors `EntityList` rows inside a `SectionCard` (settings catalogs). */
export function EntityCardRowsSkeleton({
  count = 4,
  trailing = true,
}: {
  count?: number;
  trailing?: boolean;
}) {
  return (
    <ul className="flex flex-col divide-y divide-border">
      {Array.from({ length: count }).map((_, index) => (
        <li key={index} className="px-2">
          <div className="flex min-h-11 items-center justify-between gap-3 py-3">
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-40 max-w-full" />
              <Skeleton className="mt-1.5 h-3.5 w-56 max-w-full" />
            </div>
            {trailing ? (
              <Skeleton className="h-8 w-20 shrink-0 rounded-md" />
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Mirrors `SettingsRow` (label, optional helper line, trailing control). */
export function SettingsRowsSkeleton({
  count = 4,
  control = "switch",
}: {
  count?: number;
  control?: "switch" | "button" | "text";
}) {
  return (
    <div className="divide-y divide-border">
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="flex min-h-12 flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-6"
        >
          <div className="min-w-0 flex-1">
            <Skeleton className="h-4 w-40 max-w-full" />
            <Skeleton className="mt-1.5 h-3 w-56 max-w-full" />
          </div>
          {control === "switch" ? (
            <Skeleton className="h-6 w-11 shrink-0 rounded-full" />
          ) : control === "button" ? (
            <Skeleton className="h-9 w-24 shrink-0 rounded-md" />
          ) : (
            <Skeleton className="h-4 w-20 shrink-0" />
          )}
        </div>
      ))}
    </div>
  );
}

/** Mirrors one form field: label plus input-height control. */
function FieldSkeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <Skeleton className="h-3.5 w-20" />
      <Skeleton className="h-10 w-full rounded-md" />
    </div>
  );
}

/** Mirrors `PageHeader` plus one content block, for pages that own the header. */
export function PageHeaderBlockSkeleton({
  titleWidth = "w-40",
  actions = 0,
  rows = 3,
}: {
  titleWidth?: string;
  actions?: number;
  rows?: number;
}) {
  return (
    <div>
      <LoadingLabel />
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3 sm:mb-6">
        <Skeleton className={`h-7 ${titleWidth}`} />
        {actions > 0 ? (
          <div className="flex gap-2">
            {Array.from({ length: actions }).map((_, index) => (
              <Skeleton key={index} className="h-9 w-24 rounded-md" />
            ))}
          </div>
        ) : null}
      </div>
      <div className="flex flex-col gap-3">
        {Array.from({ length: rows }).map((_, index) => (
          <Skeleton key={index} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Appointments                                                               */
/* -------------------------------------------------------------------------- */

/** Mirrors AppointmentListPage / list-table, list-stack, or calendar views. */
export function AppointmentListSkeleton({
  view = "table",
}: {
  view?: "table" | "list" | "calendar";
}) {
  if (view === "calendar") return <AppointmentCalendarSkeleton />;

  if (view === "list") {
    return (
      <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        {Array.from({ length: 5 }).map((_, index) => (
          <li key={index} className="bg-card px-5 py-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-56 max-w-full" />
                <Skeleton className="mt-1.5 h-4 w-40 max-w-full" />
              </div>
              <div className="flex items-center gap-2">
                <Skeleton className="h-5 w-20 rounded-full" />
                <Skeleton className="size-8 rounded-md" />
              </div>
            </div>
            <Skeleton className="mt-2 h-3.5 w-3/4 max-w-full" />
            <div className="mt-2 flex items-center gap-2">
              <Skeleton className="h-8 w-20 rounded-md" />
              <Skeleton className="h-8 w-24 rounded-md" />
            </div>
          </li>
        ))}
      </ul>
    );
  }

  return (
    <TableRowsSkeleton
      widths={["w-36", "w-32", "w-28", "w-24", "w-20"]}
      rows={6}
    />
  );
}

/** Mirrors AppointmentCalendarPage FullCalendar toolbar plus week grid. */
export function AppointmentCalendarSkeleton() {
  return (
    <div className="dd-calendar rounded-2xl border border-border bg-card p-2 shadow-theme-xs sm:p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 px-1 pb-3">
        <div className="flex gap-1.5">
          <Skeleton className="size-9 rounded-md" />
          <Skeleton className="size-9 rounded-md" />
          <Skeleton className="h-9 w-16 rounded-md" />
        </div>
        <Skeleton className="h-5 w-32" />
        <div className="flex gap-1.5">
          <Skeleton className="h-9 w-16 rounded-md" />
          <Skeleton className="h-9 w-16 rounded-md" />
          <Skeleton className="h-9 w-14 rounded-md" />
        </div>
      </div>
      <div className="grid grid-cols-[3.25rem_1fr] border-t border-border">
        <div />
        <div className="grid grid-cols-7">
          {Array.from({ length: 7 }).map((_, index) => (
            <div
              key={index}
              className="flex flex-col items-center gap-1 border-l border-border px-1 py-2 first:border-l-0"
            >
              <Skeleton className="h-3 w-8" />
              <Skeleton className="h-6 w-6 rounded-full" />
            </div>
          ))}
        </div>
      </div>
      <div className="grid h-[1199px] grid-cols-[3.25rem_1fr] border-t border-border">
        <div className="relative">
          {Array.from({ length: 24 }).map((_, index) => (
            <Skeleton
              key={index}
              className="absolute right-2 h-2.5 w-7"
              style={{ top: `${(index / 24) * 100 + 1}%` }}
            />
          ))}
        </div>
        <div className="grid grid-cols-7 divide-x divide-border border-l border-border">
          {Array.from({ length: 7 }).map((_, column) => (
            <div key={column} className="relative">
              {Array.from({ length: 24 }).map((_, row) => (
                <div key={row} className="h-[49px] border-b border-border" />
              ))}
              <Skeleton
                className="absolute inset-x-1 h-14 rounded-md"
                style={{ top: `${(column % 3) * 4 + 2}%` }}
              />
              <Skeleton
                className="absolute inset-x-1 h-10 rounded-md"
                style={{ top: `${(column % 4) * 5 + 30}%` }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Patients                                                                   */
/* -------------------------------------------------------------------------- */

/** Mirrors PatientListPage table or list rows. */
export function PatientListSkeleton({
  view = "table",
}: {
  view?: "table" | "list";
}) {
  if (view === "list") {
    return (
      <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        {Array.from({ length: 6 }).map((_, index) => (
          <li
            key={index}
            className="flex min-h-[44px] items-center gap-3 px-5 py-3"
          >
            <IdentityRowSkeleton />
          </li>
        ))}
      </ul>
    );
  }
  return (
    <TableRowsSkeleton
      widths={["w-40", "w-20", "w-24", "w-28"]}
      rows={6}
      identityFirstColumn
    />
  );
}

/** Mirrors the full PatientDetailPage shell: back link, header, tabs, body. */
export function PatientDetailSkeleton({
  section = "overview",
}: {
  section?:
    | "overview"
    | "records"
    | "timeline"
    | "prescriptions"
    | "billing"
    | "orders"
    | "documents"
    | "activity";
}) {
  return (
    <div className="mx-auto w-full max-w-6xl">
      <LoadingLabel />
      <div className="mb-3 flex items-center gap-1">
        <Skeleton className="size-4 rounded" />
        <Skeleton className="h-4 w-16" />
      </div>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3 sm:mb-6">
        <div className="flex min-w-0 items-start gap-3">
          <Skeleton className="size-10 shrink-0 rounded-full" />
          <div className="min-w-0">
            <Skeleton className="h-7 w-56 max-w-full" />
            <Skeleton className="mt-2 h-4 w-72 max-w-full" />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-9 w-20 rounded-md" />
          ))}
        </div>
      </div>
      <div className="mb-4 flex gap-1 overflow-x-auto">
        {Array.from({ length: 7 }).map((_, index) => (
          <Skeleton key={index} className="h-9 w-20 shrink-0 rounded-md" />
        ))}
      </div>
      {section === "overview" ? <PatientOverviewSkeleton /> : null}
      {section === "records" ? <PatientRecordsSkeleton /> : null}
      {section === "timeline" ? <PatientRowsSkeleton count={4} /> : null}
      {section === "prescriptions" ? (
        <PatientRowsSkeleton count={3} columns={3} tall />
      ) : null}
      {section === "billing" ? <PatientBillingSkeleton /> : null}
      {section === "orders" ? <PatientRowsSkeleton count={2} tall /> : null}
      {section === "documents" ? (
        <PatientRowsSkeleton count={2} columns={3} tall />
      ) : null}
      {section === "activity" ? (
        <div className="rounded-lg border border-border bg-card">
          <div className="flex items-center gap-2 px-5 py-4 sm:px-6">
            <Skeleton className="size-4 rounded" />
            <Skeleton className="h-5 w-20" />
          </div>
          <div className="border-t border-border px-5 py-4 sm:px-6">
            <ActivityTrailSkeleton count={4} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

/** Mirrors the PatientDetailPage "billing" tab stack. */
export function PatientBillingSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <PatientEligibilityCardSkeleton />
      <PatientMembershipCardSkeleton />
      <section className="mb-8">
        <Skeleton className="mb-2 h-4 w-20" />
        <div className="rounded-lg border border-border bg-card px-5 py-4 shadow-theme-xs sm:px-6">
          <ActivityTrailSkeleton count={2} />
        </div>
      </section>
    </div>
  );
}

/** Mirrors PatientDetailPage "overview": demographics, medical info, vitals. */
export function PatientOverviewSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <section className="mb-8">
        <Skeleton className="mb-2 h-4 w-28" />
        <div className="grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <FieldSkeleton key={index} />
          ))}
          <div className="col-span-full flex items-center gap-2">
            <Skeleton className="size-4 rounded" />
            <Skeleton className="h-4 w-36" />
          </div>
          <Skeleton className="h-9 w-16 rounded-md" />
        </div>
      </section>

      <section className="mb-8">
        <Skeleton className="mb-2 h-4 w-28" />
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <Skeleton className="size-4 rounded" />
            <Skeleton className="h-4 w-32" />
          </div>
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="flex flex-col gap-1.5">
              <Skeleton className="h-3.5 w-20" />
              <div className="flex gap-1">
                <Skeleton className="h-7 w-20 rounded-md" />
                <Skeleton className="h-7 w-24 rounded-md" />
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-10 flex-1 rounded-md" />
                <Skeleton className="h-10 w-16 rounded-md" />
              </div>
            </div>
          ))}
          <Skeleton className="h-9 w-40 rounded-md" />
        </div>
      </section>

      <section className="mb-8">
        <Skeleton className="mb-2 h-4 w-16" />
        <div className="rounded-lg border border-border bg-card px-5 py-4 sm:px-6">
          <div className="flex flex-col divide-y divide-border">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="py-2 first:pt-0 last:pb-0">
                <Skeleton className="h-4 w-2/3 max-w-full" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

/** Mirrors PatientDetailPage "records": charts, labs, files. */
export function PatientRecordsSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <section>
        <Skeleton className="mb-2 h-4 w-16" />
        <PatientChartListSkeleton />
      </section>
      <section>
        <Skeleton className="mb-2 h-4 w-12" />
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <FieldSkeleton className="min-w-0 flex-1" />
            <div className="flex flex-col gap-1.5">
              <Skeleton className="h-3.5 w-10" />
              <Skeleton className="h-10 w-full rounded-md sm:w-36" />
            </div>
            <Skeleton className="h-10 w-14 rounded-md" />
          </div>
          <div className="rounded-lg border border-border bg-card px-5 py-4 sm:px-6">
            <div className="flex flex-col divide-y divide-border">
              {Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="flex flex-col gap-2 py-3">
                  <div className="flex items-center justify-between gap-2">
                    <Skeleton className="h-4 w-40" />
                    <Skeleton className="h-8 w-28 rounded-md" />
                  </div>
                  <Skeleton className="h-10 w-full rounded-md" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
      <section>
        <Skeleton className="mb-2 h-4 w-12" />
        <div className="rounded-lg border border-border bg-card px-5 py-4 sm:px-6">
          <div className="flex flex-col gap-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="flex items-center justify-between">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-4 w-10" />
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

/** Mirrors PatientChartList rows. */
export function PatientChartListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 shadow-theme-xs sm:px-6">
      <div className="flex flex-col divide-y divide-border">
        {Array.from({ length: count }).map((_, index) => (
          <div
            key={index}
            className="flex min-h-11 items-center justify-between gap-3 py-2"
          >
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-48 max-w-full" />
              <Skeleton className="mt-1.5 h-3 w-16" />
            </div>
            <Skeleton className="h-4 w-28 shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Mirrors PatientDetailPage record rows (timeline, prescriptions, invoices). */
export function PatientRowsSkeleton({
  count = 4,
  columns = 2,
  tall = false,
}: {
  count?: number;
  columns?: 2 | 3;
  tall?: boolean;
}) {
  return (
    <div className="rounded-lg border border-border bg-card px-5 py-4 shadow-theme-xs sm:px-6">
      <div className="flex flex-col divide-y divide-border">
        {Array.from({ length: count }).map((_, index) => (
          <div
            key={index}
            className={
              tall
                ? "flex flex-col gap-2 py-3 first:pt-0 last:pb-0"
                : "flex items-center justify-between gap-2 py-2 first:pt-0 last:pb-0"
            }
          >
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-44 max-w-full" />
              {columns > 2 ? (
                <Skeleton className="mt-1.5 h-3.5 w-56 max-w-full" />
              ) : null}
            </div>
            <Skeleton className="h-4 w-24 shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Mirrors PatientEligibilityCard. */
export function PatientEligibilityCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-56 max-w-full" />
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="mt-1.5 h-4 w-40" />
          </div>
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <FieldSkeleton key={index} />
          ))}
        </div>
        <Skeleton className="h-9 w-32 rounded-md" />
      </CardContent>
    </Card>
  );
}

/** Mirrors PatientMembershipCard. */
export function PatientMembershipCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="min-w-0 flex-1">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="mt-1.5 h-4 w-48" />
          </div>
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <Skeleton className="h-9 w-40 rounded-md" />
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------------------------- */
/* Dashboard                                                                  */
/* -------------------------------------------------------------------------- */

/** Mirrors DashboardOverviewPage KPI + schedule/queue + trend/upcoming + follow-ups. */
export function DashboardOverviewSkeleton() {
  return (
    <div>
      <LoadingLabel />
      <div className="grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardContent className="flex items-start justify-between gap-3 py-5">
              <div className="flex min-w-0 flex-1 flex-col gap-1.5">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="mt-1 h-8 w-12" />
                {index === 1 || index === 3 ? (
                  <Skeleton className="h-3 w-24" />
                ) : null}
              </div>
              <Skeleton className="size-10 shrink-0 rounded-xl" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="mt-4 grid grid-cols-1 items-stretch gap-4 lg:grid-cols-3">
        <Card className="flex h-full min-w-0 flex-col lg:col-span-2">
          <CardHeader
            divided
            className="h-14 flex-row items-center justify-between py-0"
          >
            <Skeleton className="h-5 w-16" />
            <Skeleton className="h-8 w-12 rounded-md" />
          </CardHeader>
          <CardContent className="flex h-60 min-h-0 flex-col gap-0.5 overflow-hidden px-3 py-2">
            {Array.from({ length: 5 }).map((_, index) => (
              <div
                key={index}
                className="flex min-h-11 items-center gap-3 px-2 py-2"
              >
                <Skeleton className="h-4 w-14 shrink-0" />
                <div className="min-w-0 flex-1">
                  <Skeleton className="h-4 w-40 max-w-full" />
                  <Skeleton className="mt-1 h-3 w-56 max-w-full" />
                </div>
                <Skeleton className="h-5 w-20 shrink-0 rounded-full" />
              </div>
            ))}
          </CardContent>
        </Card>
        <Card className="flex h-full min-w-0 flex-col">
          <CardHeader
            divided
            className="h-14 flex-row items-center justify-between py-0"
          >
            <Skeleton className="h-5 w-14" />
            <Skeleton className="h-8 w-12 rounded-md" />
          </CardHeader>
          <CardContent className="flex h-60 min-h-0 flex-col gap-0.5 overflow-hidden px-3 py-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="flex min-h-11 items-center justify-between gap-2 px-2 py-2"
              >
                <div className="min-w-0 flex-1">
                  <Skeleton className="h-4 w-36 max-w-full" />
                  <Skeleton className="mt-1 h-3 w-28 max-w-full" />
                </div>
                <Skeleton className="h-5 w-16 shrink-0 rounded-full" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
      <div className="mt-4 grid grid-cols-1 items-stretch gap-4 lg:grid-cols-3">
        <Card className="flex h-full min-w-0 flex-col lg:col-span-2">
          <CardHeader
            divided
            className="h-14 flex-row items-center justify-between py-0"
          >
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-8 w-12 rounded-md" />
          </CardHeader>
          <CardContent className="flex h-[22rem] min-h-0 flex-col px-3 py-2 sm:px-4">
            <Skeleton className="h-full w-full rounded-lg" />
          </CardContent>
        </Card>
        <Card className="flex h-full min-w-0 flex-col">
          <CardHeader
            divided
            className="h-14 flex-row items-center justify-between py-0"
          >
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-8 w-12 rounded-md" />
          </CardHeader>
          <CardContent className="flex h-[22rem] min-h-0 flex-col gap-2 overflow-hidden px-3 py-2">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} className="h-11 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
      <div className="mt-4 grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <Card key={index} className="flex h-full min-w-0 flex-col">
            <CardHeader
              divided
              className="h-14 flex-row items-center justify-between py-0"
            >
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-8 w-12 rounded-md" />
            </CardHeader>
            <CardContent className="flex h-60 min-h-0 flex-col gap-0.5 overflow-hidden px-3 py-2">
              {Array.from({ length: 3 }).map((_, rowIndex) => (
                <div
                  key={rowIndex}
                  className="flex min-h-11 items-center justify-between gap-2 px-2 py-2"
                >
                  <Skeleton className="h-4 w-32 max-w-full" />
                  <Skeleton className="h-4 w-16 shrink-0" />
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Waiting room                                                               */
/* -------------------------------------------------------------------------- */

/** Mirrors WaitingRoomKanban: four `KanbanColumnShell`s with patient cards. */
export function WaitingRoomSkeleton() {
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {Array.from({ length: 4 }).map((_, index) => (
        <section
          key={index}
          className="flex min-w-0 flex-1 flex-col gap-2.5 rounded-2xl border border-border bg-secondary/30 p-3 lg:min-w-[240px]"
        >
          <header className="flex items-center justify-between px-1">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-5 w-7 rounded-md" />
          </header>
          <div className="flex flex-col gap-2">
            {Array.from({ length: [3, 3, 1, 0][index] ?? 2 }).map(
              (_, cardIndex) => (
                <Card key={cardIndex} className="p-3 shadow-none">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-2">
                      <Skeleton className="size-7 shrink-0 rounded-full" />
                      <Skeleton className="h-4 w-28 max-w-full" />
                    </div>
                    <Skeleton className="h-5 w-12 shrink-0 rounded-full" />
                  </div>
                  <Skeleton className="mt-1.5 h-3 w-36 max-w-full" />
                  <Skeleton className="mt-1 h-3 w-24 max-w-full" />
                  <Skeleton className="mt-3 h-8 w-full rounded-md" />
                </Card>
              ),
            )}
          </div>
        </section>
      ))}
    </div>
  );
}

/** Mirrors WaitingRoomPage below `lg`: status tabs plus one column of cards. */
export function WaitingRoomMobileSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <LoadingLabel />
      <Skeleton className="h-9 w-full rounded-lg" />
      <section className="flex min-w-0 flex-1 flex-col gap-2.5 rounded-2xl border border-border bg-secondary/30 p-3">
        <header className="flex items-center justify-between px-1">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-5 w-7 rounded-md" />
        </header>
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }).map((_, index) => (
            <Card key={index} className="p-3 shadow-none">
              <div className="flex items-start justify-between gap-2">
                <div className="flex min-w-0 items-center gap-2">
                  <Skeleton className="size-7 shrink-0 rounded-full" />
                  <Skeleton className="h-4 w-32 max-w-full" />
                </div>
                <Skeleton className="h-5 w-12 shrink-0 rounded-full" />
              </div>
              <Skeleton className="mt-1.5 h-3 w-40 max-w-full" />
              <Skeleton className="mt-1 h-3 w-28 max-w-full" />
              <Skeleton className="mt-3 h-8 w-full rounded-md" />
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Billing                                                                    */
/* -------------------------------------------------------------------------- */

/** Mirrors InvoiceListPage table or EntityRow stack. */
export function InvoiceListSkeleton({
  view = "table",
}: {
  view?: "table" | "list";
}) {
  if (view === "list") {
    return (
      <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        {Array.from({ length: 5 }).map((_, index) => (
          <li key={index} className="px-5">
            <div className="flex min-h-11 items-center justify-between gap-3 py-3">
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-32 max-w-full" />
                <Skeleton className="mt-1.5 h-3.5 w-72 max-w-full" />
              </div>
              <Skeleton className="h-5 w-20 shrink-0 rounded-full" />
            </div>
          </li>
        ))}
      </ul>
    );
  }
  return (
    <TableRowsSkeleton widths={["w-24", "w-36", "w-24", "w-20"]} rows={6} />
  );
}

/** Mirrors ClaimsPage table or EntityRow stack. */
export function ClaimsListSkeleton({
  view = "table",
}: {
  view?: "table" | "list";
}) {
  if (view === "list") {
    return (
      <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        {Array.from({ length: 5 }).map((_, index) => (
          <li key={index} className="px-5">
            <div className="flex min-h-11 items-center justify-between gap-3 py-3">
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-36 max-w-full" />
                <Skeleton className="mt-1.5 h-3.5 w-64 max-w-full" />
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Skeleton className="h-8 w-20 rounded-md" />
                <Skeleton className="h-8 w-24 rounded-md" />
              </div>
            </div>
          </li>
        ))}
      </ul>
    );
  }
  return (
    <TableRowsSkeleton
      widths={["w-36", "w-40", "w-20", "w-16", "w-24"]}
      rows={6}
    />
  );
}

/** Mirrors EligibilityChecksPage table or EntityRow stack. */
export function EligibilityListSkeleton({
  view = "table",
}: {
  view?: "table" | "list";
}) {
  if (view === "list") {
    return (
      <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        {Array.from({ length: 5 }).map((_, index) => (
          <li key={index} className="px-5">
            <div className="flex min-h-11 items-center justify-between gap-3 py-3">
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-36 max-w-full" />
                <Skeleton className="mt-1.5 h-3.5 w-64 max-w-full" />
              </div>
              <Skeleton className="h-8 w-24 shrink-0 rounded-md" />
            </div>
          </li>
        ))}
      </ul>
    );
  }
  return (
    <TableRowsSkeleton widths={["w-36", "w-36", "w-24", "w-24"]} rows={6} />
  );
}

/** Mirrors LoaRequestsPage table or EntityRow stack. */
export function LoaListSkeleton({
  view = "table",
}: {
  view?: "table" | "list";
}) {
  if (view === "list") {
    return (
      <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        {Array.from({ length: 5 }).map((_, index) => (
          <li key={index} className="px-5">
            <div className="flex min-h-11 items-center justify-between gap-3 py-3">
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-36 max-w-full" />
                <Skeleton className="mt-1.5 h-3.5 w-56 max-w-full" />
              </div>
              <Skeleton className="h-8 w-24 shrink-0 rounded-md" />
            </div>
          </li>
        ))}
      </ul>
    );
  }
  return (
    <TableRowsSkeleton widths={["w-36", "w-36", "w-20", "w-24"]} rows={6} />
  );
}

/** Mirrors InvoiceDetailPage: back link, header, line items, totals, activity. */
export function InvoiceDetailSkeleton() {
  return (
    <div className="mx-auto w-full max-w-2xl min-w-0">
      <LoadingLabel />
      <div className="mb-3 flex items-center gap-1">
        <Skeleton className="size-4 rounded" />
        <Skeleton className="h-4 w-16" />
      </div>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <Skeleton className="h-7 w-36" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
      <ul className="mb-4 flex flex-col divide-y divide-border text-sm">
        {Array.from({ length: 3 }).map((_, index) => (
          <li
            key={index}
            className="flex justify-between gap-2 py-2 first:pt-0"
          >
            <Skeleton className="h-4 w-48 max-w-full" />
            <Skeleton className="h-4 w-20 shrink-0" />
          </li>
        ))}
      </ul>
      <div className="flex flex-col gap-1.5 border-t border-border pt-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="flex justify-between">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-24" />
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Skeleton className="h-9 w-20 rounded-md" />
        <Skeleton className="h-9 w-28 rounded-md" />
      </div>
      <div className="mt-4 rounded-lg border border-border bg-card">
        <div className="flex items-center gap-2 px-5 py-4 sm:px-6">
          <Skeleton className="size-4 rounded" />
          <Skeleton className="h-5 w-24" />
        </div>
        <div className="border-t border-border px-5 py-4 sm:px-6">
          <div className="flex flex-col gap-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index}>
                <Skeleton className="h-4 w-3/4 max-w-full" />
                <Skeleton className="mt-1.5 h-3 w-40" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/** Mirrors ClaimDetailPage: back link, header, claim card. */
export function ClaimDetailSkeleton() {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <LoadingLabel />
      <div className="mb-3 flex items-center gap-1">
        <Skeleton className="size-4 rounded" />
        <Skeleton className="h-4 w-14" />
      </div>
      <div className="mb-4">
        <Skeleton className="h-7 w-24" />
        <Skeleton className="mt-2 h-4 w-64 max-w-full" />
      </div>
      <div className="rounded-lg border border-border bg-card p-5 shadow-theme-xs sm:p-6">
        <div className="flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-4 w-2/3 max-w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}

/** Mirrors the compact dashboard billing widgets. */
export function BillingWidgetSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-24" />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index}>
              <Skeleton className="h-3 w-12" />
              <Skeleton className="mt-1.5 h-5 w-20" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------------------------- */
/* Documents                                                                  */
/* -------------------------------------------------------------------------- */

/** Mirrors DocumentTemplatesPage EntityList rows. */
export function DocumentTemplatesSkeleton({ count = 4 }: { count?: number }) {
  return (
    <ul className="flex flex-col divide-y divide-border">
      {Array.from({ length: count }).map((_, index) => (
        <li key={index} className="px-2">
          <div className="flex min-h-11 items-center py-3">
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-44 max-w-full" />
              <Skeleton className="mt-1.5 h-3.5 w-64 max-w-full" />
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Mirrors DocumentNewPage template picker card. */
export function DocumentTemplatePickerSkeleton() {
  return (
    <Card>
      <CardContent className="flex flex-col gap-2 pt-5">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-9 w-full rounded-md" />
        ))}
      </CardContent>
    </Card>
  );
}

/** Mirrors patient search results in DocumentGeneratePage. */
export function DocumentSearchResultsSkeleton() {
  return (
    <ul className="flex flex-col divide-y divide-border">
      {Array.from({ length: 3 }).map((_, index) => (
        <li key={index} className="flex min-h-11 items-center py-2">
          <Skeleton className="h-4 w-48 max-w-full" />
        </li>
      ))}
    </ul>
  );
}

/* -------------------------------------------------------------------------- */
/* Audit, reports, reminders, recalls, alerts, search                         */
/* -------------------------------------------------------------------------- */

/** Mirrors AuditLogPage table or EntityRow stack. */
export function AuditLogSkeleton({
  view = "table",
}: {
  view?: "table" | "list";
}) {
  if (view === "list") {
    return (
      <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        {Array.from({ length: 6 }).map((_, index) => (
          <li key={index} className="px-5">
            <div className="flex min-h-11 items-center justify-between gap-3 py-3">
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-64 max-w-full" />
                <Skeleton className="mt-1.5 h-3.5 w-48 max-w-full" />
              </div>
              <Skeleton className="h-3 w-28 shrink-0" />
            </div>
          </li>
        ))}
      </ul>
    );
  }
  return (
    <TableRowsSkeleton widths={["w-36", "w-56", "w-28", "w-24"]} rows={6} />
  );
}

/** Mirrors ActivityTrail list rows. */
export function ActivityTrailSkeleton({ count = 3 }: { count?: number }) {
  return (
    <ul className="flex flex-col divide-y divide-border">
      {Array.from({ length: count }).map((_, index) => (
        <li key={index} className="py-2.5 first:pt-0 last:pb-0">
          <Skeleton className="h-4 w-3/4 max-w-full" />
          <Skeleton className="mt-1.5 h-3 w-48 max-w-full" />
        </li>
      ))}
    </ul>
  );
}

/** Mirrors ReportsPage `BarRow` list (8rem / 1fr / 3rem columns). */
export function ReportsSkeleton({ rows = 12 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className="grid grid-cols-[8rem_1fr_3rem] items-center gap-3"
        >
          <Skeleton className="h-3.5 w-20 max-w-full" />
          <Skeleton className="h-2 w-full rounded-full" />
          <Skeleton className="ml-auto h-4 w-6" />
        </div>
      ))}
    </div>
  );
}

/** Mirrors ReportsPage NPS response rows. */
export function NpsReportSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="flex flex-col divide-y divide-border">
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
        >
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-56 max-w-full" />
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}

/** Mirrors ReminderDashboardPage table or EntityRow stack. */
export function ReminderListSkeleton({
  view = "table",
}: {
  view?: "table" | "list";
}) {
  if (view === "list") {
    return (
      <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        {Array.from({ length: 5 }).map((_, index) => (
          <li key={index} className="px-5">
            <div className="flex min-h-11 items-center justify-between gap-3 py-3">
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-36 max-w-full" />
                <Skeleton className="mt-1.5 h-3.5 w-48 max-w-full" />
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Skeleton className="h-5 w-16 rounded-full" />
                <Skeleton className="h-8 w-16 rounded-md" />
              </div>
            </div>
          </li>
        ))}
      </ul>
    );
  }
  return (
    <TableRowsSkeleton
      widths={["w-36", "w-28", "w-20", "w-20", "w-16"]}
      rows={6}
    />
  );
}

/** Mirrors RecallsPage table or EntityRow stack. */
export function RecallsSkeleton({
  view = "table",
}: {
  view?: "table" | "list";
}) {
  if (view === "list") {
    return (
      <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        {Array.from({ length: 4 }).map((_, index) => (
          <li
            key={index}
            className="flex flex-wrap items-center justify-between gap-3 px-5 py-3"
          >
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-36 max-w-full" />
              <Skeleton className="mt-1.5 h-3.5 w-48 max-w-full" />
            </div>
            <div className="flex flex-wrap gap-2">
              <Skeleton className="h-8 w-16 rounded-md" />
              <Skeleton className="h-8 w-24 rounded-md" />
              <Skeleton className="h-8 w-20 rounded-md" />
            </div>
          </li>
        ))}
      </ul>
    );
  }
  return (
    <TableRowsSkeleton widths={["w-36", "w-24", "w-24", "w-40"]} rows={5} />
  );
}

/** Mirrors AlertsPage notification rows (36px icon, title/time, body). */
export function AlertsSkeleton({ count = 5 }: { count?: number }) {
  return (
    <ul className="divide-y divide-border rounded-lg border border-border bg-card">
      {Array.from({ length: count }).map((_, index) => (
        <li key={index} className="flex gap-3 px-4 py-3">
          <Skeleton className="mt-0.5 size-9 shrink-0 rounded-full" />
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <Skeleton className="h-4 w-48 max-w-full" />
              <Skeleton className="h-3 w-12 shrink-0" />
            </div>
            <Skeleton className="mt-1.5 h-3.5 w-3/4 max-w-full" />
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Mirrors the NotificationBell popover/sheet list. */
export function NotificationBellListSkeleton({
  count = 4,
}: {
  count?: number;
}) {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <li key={index} className="flex gap-3 px-3 py-3">
          <Skeleton className="mt-0.5 size-8 shrink-0 rounded-full" />
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <Skeleton className="h-4 w-36 max-w-full" />
              <Skeleton className="h-3 w-10 shrink-0" />
            </div>
            <Skeleton className="mt-1.5 h-3 w-3/4 max-w-full" />
          </div>
        </li>
      ))}
    </>
  );
}

/** Mirrors ChartSearchPage result rows. */
export function ChartSearchSkeleton() {
  return (
    <ul className="flex flex-col divide-y divide-border">
      {Array.from({ length: 4 }).map((_, index) => (
        <li key={index} className="py-3 first:pt-0 last:pb-0">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Skeleton className="h-4 w-40 max-w-full" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="mt-2 h-3.5 w-full" />
          <Skeleton className="mt-1.5 h-3.5 w-4/5 max-w-full" />
          <Skeleton className="mt-2 h-4 w-20" />
        </li>
      ))}
    </ul>
  );
}

/* -------------------------------------------------------------------------- */
/* Settings                                                                   */
/* -------------------------------------------------------------------------- */

/** Mirrors AssistantSettingsPage: enable switch plus five tool switches. */
export function AssistantSettingsSkeleton() {
  return (
    <div className="divide-y divide-border">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="flex min-h-12 items-center justify-between gap-6 py-3"
        >
          <Skeleton className="h-4 w-40 max-w-full" />
          <Skeleton className="h-6 w-11 shrink-0 rounded-full" />
        </div>
      ))}
    </div>
  );
}

/** Mirrors DoctorProfilePage form. */
export function DoctorProfileSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <LoadingLabel />
      <FieldSkeleton />
      <FieldSkeleton />
      <div className="grid grid-cols-2 gap-3">
        <FieldSkeleton />
        <FieldSkeleton />
      </div>
      <div className="flex flex-col gap-1.5">
        <Skeleton className="h-3.5 w-16" />
        <Skeleton className="h-28 w-full rounded-lg" />
      </div>
      <div className="flex flex-col gap-1.5">
        <Skeleton className="h-3.5 w-20" />
        <Skeleton className="h-28 w-full rounded-lg" />
      </div>
      <Skeleton className="h-9 w-20 rounded-md" />
    </div>
  );
}

/** Mirrors ClinicSettingsPage per settings view. */
export function ClinicSettingsSkeleton({
  view = "details",
}: {
  view?: "details" | "hours" | "rooms" | "branding" | "compliance";
}) {
  if (view === "hours") {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <Skeleton className="mb-2 h-4 w-16" />
          <div className="flex flex-col divide-y divide-border rounded-lg border border-border">
            {Array.from({ length: 7 }).map((_, index) => (
              <div
                key={index}
                className="flex flex-wrap items-center gap-3 px-3 py-2.5"
              >
                <Skeleton className="h-4 w-20 shrink-0" />
                <Skeleton className="h-9 w-32 rounded-md" />
                <Skeleton className="h-9 w-32 rounded-md" />
                <div className="ml-auto flex items-center gap-2">
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-6 w-11 rounded-full" />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <Skeleton className="h-3.5 w-40" />
          <Skeleton className="h-20 w-full rounded-md" />
        </div>
        <Skeleton className="h-9 w-20 rounded-md" />
      </div>
    );
  }

  if (view === "branding") {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <Skeleton className="mb-2 h-4 w-20" />
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Skeleton className="h-3.5 w-10" />
              <Skeleton className="h-36 w-full rounded-lg" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Skeleton className="h-3.5 w-24" />
              <Skeleton className="h-10 w-full rounded-md" />
            </div>
          </div>
        </div>
        <Skeleton className="h-9 w-20 rounded-md" />
      </div>
    );
  }

  if (view === "compliance") {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <Skeleton className="mb-2 h-4 w-36" />
          <div className="flex flex-col gap-4">
            <FieldSkeleton />
            <FieldSkeleton />
            <div className="flex flex-col gap-2">
              <Skeleton className="h-3.5 w-20" />
              <Skeleton className="h-2 w-full rounded-full" />
            </div>
          </div>
        </div>
        <Skeleton className="h-9 w-20 rounded-md" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Skeleton className="mb-2 h-4 w-16" />
        <div className="flex flex-col gap-4">
          <FieldSkeleton />
          <FieldSkeleton />
          <div className="grid gap-3 sm:grid-cols-2">
            <FieldSkeleton />
            <FieldSkeleton />
          </div>
          <FieldSkeleton />
          <div className="flex items-center justify-between gap-3">
            <Skeleton className="h-4 w-48 max-w-full" />
            <Skeleton className="h-6 w-11 shrink-0 rounded-full" />
          </div>
        </div>
      </div>
      <Skeleton className="h-9 w-20 rounded-md" />
    </div>
  );
}

/** Mirrors NotificationsSettingsPage channel/reminder/question rows. */
export function NotificationsSettingsSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <LoadingLabel />
      <div>
        <Skeleton className="mb-2 h-4 w-20" />
        <SettingsRowsSkeleton count={3} />
      </div>
      <div>
        <Skeleton className="mb-2 h-4 w-20" />
        <SettingsRowsSkeleton count={4} />
      </div>
      <div>
        <Skeleton className="mb-2 h-4 w-24" />
        <div className="grid gap-3 py-3 sm:grid-cols-[2fr_1fr_auto] sm:items-end">
          <FieldSkeleton />
          <FieldSkeleton />
          <Skeleton className="h-10 w-16 rounded-md" />
        </div>
      </div>
      <Skeleton className="h-9 w-20 rounded-md" />
    </div>
  );
}

/** Mirrors AccountSettingsPage session rows plus action rows. */
export function AccountSettingsSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <LoadingLabel />
      <div>
        <Skeleton className="mb-2 h-4 w-16" />
        <SettingsRowsSkeleton count={2} control="text" />
        <SettingsRowsSkeleton count={1} control="button" />
      </div>
      <div>
        <Skeleton className="mb-2 h-4 w-14" />
        <SettingsRowsSkeleton count={2} control="button" />
      </div>
    </div>
  );
}

/** Mirrors TeamSettingsPage member rows, including trailing role controls. */
export function TeamSettingsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <ul className="flex flex-col divide-y divide-border">
      {Array.from({ length: count }).map((_, index) => (
        <li key={index} className="px-2">
          <div className="flex min-h-11 items-center justify-between gap-3 py-3">
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-40 max-w-full" />
              <Skeleton className="mt-1.5 h-3.5 w-56 max-w-full" />
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Skeleton className="h-8 w-[110px] rounded-md" />
              <Skeleton className="h-8 w-20 rounded-md" />
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Mirrors ServicesSettingsPage / Payers / Membership plans rows. */
export function ServicesListSkeleton({
  count = 4,
  trailing = true,
}: {
  count?: number;
  trailing?: boolean;
}) {
  return <EntityCardRowsSkeleton count={count} trailing={trailing} />;
}

/** Mirrors Memberships list rows (name, price line, edit action). */
export function MembershipPlansSkeleton({ count = 4 }: { count?: number }) {
  return (
    <ul className="flex flex-col divide-y divide-border">
      {Array.from({ length: count }).map((_, index) => (
        <li key={index} className="px-2">
          <div className="flex min-h-11 items-center justify-between gap-3 py-3">
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-36 max-w-full" />
              <Skeleton className="mt-1.5 h-3.5 w-48 max-w-full" />
            </div>
            <Skeleton className="h-8 w-14 shrink-0 rounded-md" />
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Mirrors DocumentTemplatesPage in Settings (catalog rows). */
export function SettingsCatalogSkeleton({ count = 4 }: { count?: number }) {
  return <EntityCardRowsSkeleton count={count} trailing={false} />;
}

export function PayersListSkeleton({ count = 4 }: { count?: number }) {
  return <EntityCardRowsSkeleton count={count} />;
}

/** Mirrors organization / billing plan settings rows. */
export function PlanSettingsSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <LoadingLabel />
      <div>
        <SettingsRowsSkeleton count={2} control="text" />
      </div>
      <div>
        <Skeleton className="mb-2 h-4 w-16" />
        <ul className="flex flex-col gap-2">
          {Array.from({ length: 2 }).map((_, index) => (
            <li
              key={index}
              className="flex items-center justify-between gap-2 py-2"
            >
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-4 w-16" />
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Platform                                                                   */
/* -------------------------------------------------------------------------- */

/** Mirrors PlatformShell chrome plus one content block. */
export function PlatformShellSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
        <Skeleton className="h-5 w-20" />
        <div className="flex gap-3">
          <Skeleton className="h-4 w-14" />
          <Skeleton className="h-4 w-10" />
          <Skeleton className="h-4 w-14" />
        </div>
        <Skeleton className="ml-auto h-8 w-20 rounded-md" />
      </div>
      <div className="p-4 sm:p-6">
        <Skeleton className="mb-4 h-7 w-40" />
        <div className="flex flex-col gap-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}

/** Mirrors PlatformTenantsPage table or EntityRow stack. */
export function PlatformTenantsSkeleton({
  view = "table",
}: {
  view?: "table" | "list";
}) {
  if (view === "list") {
    return (
      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
        <EntityRowsSkeleton count={5} trailing={false} />
      </div>
    );
  }
  return (
    <TableRowsSkeleton widths={["w-44", "w-20", "w-16", "w-20"]} rows={6} />
  );
}

/** Mirrors PlatformTenantDetailPage card. */
export function PlatformTenantDetailSkeleton() {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <LoadingLabel />
      <Skeleton className="mb-3 h-8 w-16 rounded-md" />
      <div className="mb-4">
        <Skeleton className="h-7 w-48 max-w-full" />
      </div>
      <div className="rounded-lg border border-border bg-card p-5 shadow-theme-xs sm:p-6">
        <div className="flex flex-col gap-4">
          <Skeleton className="h-4 w-40" />
          <div className="flex flex-wrap gap-2">
            <Skeleton className="h-9 w-24 rounded-md" />
            <Skeleton className="h-9 w-20 rounded-md" />
            <Skeleton className="h-9 w-16 rounded-md" />
            <Skeleton className="h-9 w-16 rounded-md" />
          </div>
          <div className="flex flex-col gap-2">
            {Array.from({ length: 2 }).map((_, index) => (
              <Skeleton key={index} className="h-14 w-full rounded-md" />
            ))}
          </div>
          <Skeleton className="h-9 w-32 rounded-md" />
        </div>
      </div>
    </div>
  );
}

/** Mirrors PlatformMetricsPage metric cards and clinics card. */
export function PlatformMetricsSkeleton() {
  return (
    <div>
      <LoadingLabel />
      <div className="grid gap-3 sm:grid-cols-2">
        {Array.from({ length: 6 }).map((_, index) => (
          <Card key={index}>
            <CardContent className="pt-5">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="mt-2 h-7 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="mt-4">
        <CardContent className="flex flex-col gap-1 pt-5">
          <Skeleton className="mb-2 h-4 w-16" />
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-4 w-40 max-w-full" />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Patient portal and public pages                                            */
/* -------------------------------------------------------------------------- */

/** Mirrors PatientPortalVisitsPage visit cards. */
export function PortalVisitsSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="flex flex-col gap-3">
      <LoadingLabel />
      {Array.from({ length: count }).map((_, index) => (
        <Card key={index}>
          <CardContent className="flex items-start justify-between gap-3 py-4">
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-40 max-w-full" />
              <Skeleton className="mt-1.5 h-4 w-56 max-w-full" />
            </div>
            <Skeleton className="h-5 w-16 shrink-0 rounded-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/** Mirrors PatientPortalDocumentsPage document cards. */
export function PortalDocumentsSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="flex flex-col gap-3">
      <LoadingLabel />
      {Array.from({ length: count }).map((_, index) => (
        <Card key={index}>
          <CardContent className="flex items-center justify-between gap-3 py-4">
            <div className="flex min-w-0 items-center gap-3">
              <Skeleton className="size-5 shrink-0 rounded" />
              <div className="min-w-0">
                <Skeleton className="h-4 w-40 max-w-full" />
                <Skeleton className="mt-1.5 h-3 w-24" />
              </div>
            </div>
            <Skeleton className="h-8 w-28 shrink-0 rounded-md" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/** Mirrors PatientPortalInvoicesPage balance banner plus invoice cards. */
export function PortalInvoicesSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="flex flex-col gap-4">
      <LoadingLabel />
      <Card>
        <CardContent className="py-3">
          <Skeleton className="h-4 w-64 max-w-full" />
        </CardContent>
      </Card>
      <div className="flex flex-col gap-3">
        {Array.from({ length: count }).map((_, index) => (
          <Card key={index}>
            <CardContent className="flex items-center justify-between gap-3 py-4">
              <div className="min-w-0 flex-1">
                <Skeleton className="h-4 w-32 max-w-full" />
                <Skeleton className="mt-1.5 h-4 w-56 max-w-full" />
              </div>
              <Skeleton className="h-5 w-16 shrink-0 rounded-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

/** Mirrors Sonar chart / referral chart diagnoses + vitals table. */
export function PortalChartSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <LoadingLabel />
      <section>
        <Skeleton className="mb-2 h-4 w-24" />
        <div className="flex flex-col gap-3">
          {Array.from({ length: 2 }).map((_, index) => (
            <Card key={index}>
              <CardContent className="py-4">
                <Skeleton className="h-4 w-48 max-w-full" />
                <Skeleton className="mt-1.5 h-4 w-64 max-w-full" />
                <Skeleton className="mt-2 h-3 w-56 max-w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
      <section>
        <Skeleton className="mb-2 h-4 w-24" />
        <div className="overflow-hidden rounded-lg border border-border">
          <div className="grid grid-cols-5 gap-2 bg-muted/50 px-3 py-2">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-3 w-12" />
            ))}
          </div>
          {Array.from({ length: 4 }).map((_, rowIndex) => (
            <div
              key={rowIndex}
              className="grid grid-cols-5 gap-2 border-t border-border px-3 py-2.5"
            >
              {Array.from({ length: 5 }).map((_, columnIndex) => (
                <Skeleton key={columnIndex} className="h-4 w-14" />
              ))}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

/** Mirrors PublicBookingPage form below AuthLayout. */
export function PublicBookingSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <LoadingLabel />
      <Skeleton className="h-4 w-56 max-w-full" />
      <div className="flex flex-col gap-1.5">
        <Skeleton className="h-3.5 w-12" />
        <Skeleton className="h-10 w-full rounded-md" />
      </div>
      <div className="flex flex-col gap-1.5">
        <Skeleton className="h-3.5 w-20" />
        <Skeleton className="h-10 w-full rounded-md" />
      </div>
      <div className="flex flex-col gap-1.5">
        <Skeleton className="h-3.5 w-28" />
        <Skeleton className="h-10 w-full rounded-md" />
      </div>
      <Skeleton className="h-11 w-full rounded-md" />
    </div>
  );
}

/** Mirrors OnboardingPage: brand mark, stepper, and form card. */
export function OnboardingSkeleton() {
  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <LoadingLabel />
      <div className="flex items-center justify-center gap-2">
        <Skeleton className="size-9 rounded-xl" />
        <Skeleton className="h-6 w-28" />
      </div>
      <div className="flex items-center justify-between gap-2">
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="flex flex-1 items-center gap-2">
            <Skeleton className="size-7 shrink-0 rounded-full" />
            <Skeleton className="h-3 w-12" />
          </div>
        ))}
      </div>
      <div className="rounded-lg border border-border bg-card shadow-theme-sm">
        <div className="border-b border-border px-5 py-4 sm:px-6">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="mt-2 h-4 w-64 max-w-full" />
        </div>
        <div className="flex flex-col gap-4 px-5 py-4 sm:px-6">
          <FieldSkeleton />
          <FieldSkeleton />
          <Skeleton className="h-10 w-full rounded-md" />
          <Skeleton className="h-9 w-28 rounded-md" />
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* SOAP                                                                       */
/* -------------------------------------------------------------------------- */

/** Mirrors SoapNotePage: header, versions, template, specialty, S/O/A/P, actions. */
export function SoapNoteSkeleton() {
  return (
    <div className="flex w-full flex-col gap-4">
      <LoadingLabel />
      <div className="mb-2">
        <Skeleton className="h-7 w-32" />
        <Skeleton className="mt-2 h-4 w-56 max-w-full" />
      </div>
      <div className="rounded-lg border border-border bg-card px-5 py-4 shadow-theme-xs sm:px-6">
        <Skeleton className="h-9 w-24 rounded-md" />
      </div>
      <div className="h-[10.25rem] rounded-lg border border-dashed border-border p-4">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="mt-3 h-20 w-full rounded-md" />
        <Skeleton className="mt-3 h-8 w-16 rounded-md" />
      </div>
      <div className="flex flex-col gap-1.5">
        <Skeleton className="h-3.5 w-16" />
        <Skeleton className="h-10 w-full rounded-md" />
      </div>
      <section className="flex flex-col gap-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="flex flex-col gap-1.5">
            <Skeleton className="h-3.5 w-24" />
            <Skeleton className="h-20 w-full rounded-md" />
          </div>
        ))}
        <FieldSkeleton />
        <FieldSkeleton />
        <FieldSkeleton />
      </section>
      <div className="flex gap-2">
        <Skeleton className="h-9 w-20 rounded-md" />
        <Skeleton className="h-9 w-28 rounded-md" />
      </div>
      <div className="rounded-lg border border-border bg-card">
        <div className="flex items-center gap-2 px-5 py-4 sm:px-6">
          <Skeleton className="size-4 rounded" />
          <Skeleton className="h-5 w-20" />
        </div>
        <div className="border-t border-border px-5 py-4 sm:px-6">
          <ActivityTrailSkeleton count={3} />
        </div>
      </div>
    </div>
  );
}
