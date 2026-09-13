import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

function RowLines({ count }: { count: number }) {
  return (
    <div className="flex flex-col divide-y divide-border">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex items-center justify-between gap-3 px-5 py-4"
        >
          <div className="flex min-w-0 flex-1 flex-col gap-2">
            <Skeleton className="h-4 w-2/5" />
            <Skeleton className="h-3 w-1/3" />
          </div>
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
      ))}
    </div>
  );
}

/** Mirrors AppointmentListPage list card. */
export function AppointmentListSkeleton() {
  return <RowLines count={5} />;
}

/** Mirrors PatientListPage table. */
export function PatientListSkeleton() {
  return (
    <div className="p-5">
      <div className="mb-3 grid grid-cols-3 gap-4">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-16" />
      </div>
      <div className="flex flex-col gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  );
}

/** Mirrors PatientDetailPage header + tab panel. */
export function PatientDetailSkeleton() {
  return (
    <div className="mx-auto w-full">
      <Skeleton className="h-4 w-20" />
      <Skeleton className="mt-4 h-8 w-64" />
      <Skeleton className="mt-2 h-4 w-40" />
      <div className="mt-6 flex gap-2">
        <Skeleton className="h-9 w-24 rounded-lg" />
        <Skeleton className="h-9 w-24 rounded-lg" />
        <Skeleton className="h-9 w-24 rounded-lg" />
      </div>
      <Skeleton className="mt-4 h-48 w-full rounded-2xl" />
    </div>
  );
}

/** Mirrors WaitingRoomPage 4-column board. */
export function WaitingRoomSkeleton() {
  return (
    <div className="flex gap-3 overflow-hidden">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="flex min-w-[240px] flex-1 flex-col gap-2.5 rounded-2xl border border-border bg-secondary/30 p-3"
        >
          <div className="flex items-center justify-between px-1">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-5 w-8 rounded-full" />
          </div>
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-24 w-full rounded-xl" />
        </div>
      ))}
    </div>
  );
}

/** Mirrors WaitingRoomPage mobile column list. */
export function WaitingRoomMobileSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-9 w-full rounded-lg" />
      <Skeleton className="h-28 w-full rounded-xl" />
      <Skeleton className="h-28 w-full rounded-xl" />
      <Skeleton className="h-28 w-full rounded-xl" />
    </div>
  );
}

/** Mirrors DashboardOverviewPage KPI + today/queue + trend/agenda + attention. */
export function DashboardOverviewSkeleton() {
  return (
    <div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="flex items-start justify-between gap-3 py-5">
              <div className="flex flex-col gap-2">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-8 w-12" />
              </div>
              <Skeleton className="size-10 rounded-xl" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="mt-4 grid grid-cols-1 items-stretch gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <Skeleton className="h-5 w-16" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-11 w-full" />
            <Skeleton className="mt-2 h-11 w-full" />
            <Skeleton className="mt-2 h-11 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-16" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-11 w-full" />
            <Skeleton className="mt-2 h-11 w-full" />
          </CardContent>
        </Card>
      </div>
      <div className="mt-4 grid grid-cols-1 items-stretch gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <Skeleton className="h-5 w-48" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-24" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-16 w-full" />
            <Skeleton className="mt-2 h-16 w-full" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/** Mirrors InvoiceDetailPage header + body. */
export function InvoiceDetailSkeleton() {
  return (
    <div className="mx-auto max-w-2xl">
      <Skeleton className="h-4 w-20" />
      <Skeleton className="mt-4 h-8 w-48" />
      <Skeleton className="mt-4 h-48 w-full rounded-2xl" />
    </div>
  );
}

/** Mirrors PublicBookingPage form card. */
export function PublicBookingSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
  );
}

/** Mirrors ChartSearchPage result cards. */
export function ChartSearchSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-20 w-full rounded-xl" />
      <Skeleton className="h-20 w-full rounded-xl" />
      <Skeleton className="h-20 w-full rounded-xl" />
    </div>
  );
}

/** Mirrors ReportsPage bar list. */
export function ReportsSkeleton() {
  return (
    <div className="flex flex-col gap-3 p-1">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}

/** Mirrors AssistantSettingsPage switch row. */
export function AssistantSettingsSkeleton() {
  return (
    <div className="flex items-center justify-between py-1">
      <Skeleton className="h-4 w-40" />
      <Skeleton className="h-6 w-11 rounded-full" />
    </div>
  );
}

/** Mirrors DoctorProfilePage form card. */
export function DoctorProfileSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-24" />
    </div>
  );
}

/** Mirrors AuditLogPage entry list. */
export function AuditLogSkeleton() {
  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full rounded-lg" />
      ))}
    </div>
  );
}

/** Mirrors ActivityTrail card body. */
export function ActivityTrailSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-3 w-1/3" />
    </div>
  );
}

/** Mirrors OnboardingPage stepper card. */
export function OnboardingSkeleton() {
  return (
    <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-theme-xs">
      <Skeleton className="h-6 w-40" />
      <Skeleton className="mt-2 h-4 w-64" />
      <Skeleton className="mt-6 h-10 w-full" />
      <Skeleton className="mt-3 h-10 w-full" />
      <Skeleton className="mt-6 h-10 w-28" />
    </div>
  );
}

/** Mirrors RecallsPage list. */
export function RecallsSkeleton() {
  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full rounded-lg" />
      ))}
    </div>
  );
}

/** Mirrors InvoiceListPage filter + list. */
export function InvoiceListSkeleton() {
  return <RowLines count={5} />;
}

/** Mirrors ReminderDashboardPage list. */
export function ReminderListSkeleton() {
  return <RowLines count={5} />;
}

/** Mirrors ClaimsListPage list. */
export function ClaimsListSkeleton() {
  return <RowLines count={5} />;
}

/** Mirrors EligibilityChecksPage list. */
export function EligibilityListSkeleton() {
  return <RowLines count={5} />;
}

/** Mirrors LoaRequestsPage list. */
export function LoaListSkeleton() {
  return <RowLines count={5} />;
}

/** Mirrors PayersSettingsPage list. */
export function PayersListSkeleton() {
  return <RowLines count={4} />;
}

/** Mirrors ClaimDetailPage body. */
export function ClaimsPageSkeleton() {
  return <RowLines count={3} />;
}

/** Mirrors ServicesSettingsPage catalog list. */
export function ServicesListSkeleton() {
  return <RowLines count={4} />;
}

/** Mirrors DocumentTemplatesPage catalog. */
export function DocumentTemplatesSkeleton() {
  return (
    <div className="flex flex-col gap-2 p-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full rounded-lg" />
      ))}
    </div>
  );
}

/** Mirrors TeamSettingsPage member rows. */
export function TeamSettingsSkeleton() {
  return <RowLines count={4} />;
}

/** Mirrors AppointmentCalendarPage toolbar + grid. */
export function AppointmentCalendarSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        <Skeleton className="h-9 w-36 rounded-lg" />
        <Skeleton className="h-9 w-28 rounded-lg" />
        <Skeleton className="h-9 w-24 rounded-lg" />
      </div>
      <Skeleton className="h-[420px] w-full rounded-2xl" />
    </div>
  );
}

/** Mirrors ClinicSettingsPage stacked cards. */
export function ClinicSettingsSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <Skeleton className="h-56 w-full rounded-2xl" />
      <Skeleton className="h-40 w-full rounded-2xl" />
      <Skeleton className="h-32 w-full rounded-2xl" />
    </div>
  );
}

/** Mirrors NotificationsSettingsPage form. */
export function NotificationsSettingsSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-2/3" />
      <Skeleton className="h-10 w-24" />
    </div>
  );
}

/** Mirrors SoapNotePage form cards. */
export function SoapNoteSkeleton() {
  return (
    <div className="flex w-full flex-col gap-4">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-28 w-full rounded-2xl" />
      <Skeleton className="h-64 w-full rounded-2xl" />
    </div>
  );
}
