import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { BarChart3, Download } from "lucide-react";
import { api } from "@/lib/apiClient";
import { API_BASE } from "@/lib/apiBase";
import { getAccessToken, getClinicId } from "@/lib/auth";
import { SectionHeaderActions } from "@/components/layout/SectionHeaderActions";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DateRangePicker } from "@/components/ui/date-picker";
import { Progress } from "@/components/ui/progress";
import { SegmentedControl } from "@/components/ui/sliding-tabs";
import { parseIsoDate, toIsoDate, todayIsoManila } from "@/lib/isoDate";
import { ReportsSkeleton } from "@/components/skeletons/PageSkeletons";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const REPORTS = [
  { key: "appointments", label: "Appointments" },
  { key: "revenue", label: "Revenue" },
  { key: "patient-growth", label: "Patient growth" },
  { key: "top-diagnoses", label: "Top diagnoses" },
  { key: "nps", label: "NPS" },
] as const;

type ReportKey = (typeof REPORTS)[number]["key"];

function defaultRange() {
  const to = todayIsoManila();
  const toDate = parseIsoDate(to);
  if (!toDate) return { from: to, to };
  const fromDate = new Date(toDate);
  fromDate.setDate(fromDate.getDate() - 30);
  return { from: toIsoDate(fromDate), to };
}

function BarRow({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  const width = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="grid grid-cols-[8rem_1fr_3rem] items-center gap-3 text-sm">
      <span className="truncate text-muted-foreground">{label}</span>
      <Progress value={width} className="h-2" />
      <span className="text-right font-medium text-foreground">{value}</span>
    </div>
  );
}

export function ReportsPage() {
  const defaults = useMemo(() => defaultRange(), []);
  const [report, setReport] = useState<ReportKey>("appointments");
  const [fromDate, setFromDate] = useState(defaults.from);
  const [toDate, setToDate] = useState(defaults.to);
  const [groupBy, setGroupBy] = useState("day");

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["report", report, fromDate, toDate, groupBy],
    queryFn: () => {
      const params = {
        from_date: fromDate,
        to_date: toDate,
        group_by: groupBy,
      };
      if (report === "appointments") return api.getAppointmentsReport(params);
      if (report === "revenue") return api.getRevenueReport(params);
      if (report === "patient-growth")
        return api.getPatientGrowthReport(params);
      return api.getTopDiagnosesReport({
        from_date: fromDate,
        to_date: toDate,
      });
    },
    enabled: report !== "nps",
  });

  const {
    data: npsData,
    isLoading: npsLoading,
    isError: npsError,
    refetch: refetchNps,
  } = useQuery({
    queryKey: ["report-nps", fromDate, toDate],
    queryFn: () => api.getNpsReport({ from_date: fromDate, to_date: toDate }),
    enabled: report === "nps",
  });

  const series = data?.series ?? [];
  const maxValue = useMemo(() => {
    if (!series.length) return 0;
    if (report === "appointments") {
      return Math.max(...series.map((r) => Number(r.booked ?? 0)));
    }
    if (report === "revenue") {
      return Math.max(...series.map((r) => Number(r.amount ?? 0)));
    }
    if (report === "patient-growth") {
      return Math.max(
        ...series.map(
          (r) =>
            Number(r.new_patients ?? 0) + Number(r.returning_patients ?? 0),
        ),
      );
    }
    return Math.max(...series.map((r) => Number(r.visit_count ?? 0)));
  }, [series, report]);

  async function exportCsv() {
    const token = getAccessToken();
    const clinicId = getClinicId();
    const qs = new URLSearchParams({
      from_date: fromDate,
      to_date: toDate,
      group_by: groupBy,
    });
    const res = await fetch(`${API_BASE}/reports/${report}/export.csv?${qs}`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(clinicId ? { "X-Clinic-Id": clinicId } : {}),
      },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      {report !== "nps" && (
        <SectionHeaderActions>
          <Button variant="outline" size="sm" onClick={exportCsv}>
            <Download className="size-4" />
            Export CSV
          </Button>
        </SectionHeaderActions>
      )}

      <div className="mb-4">
        <SegmentedControl
          value={report}
          onChange={setReport}
          size="compact"
          aria-label="Report type"
          options={REPORTS.map((r) => ({ value: r.key, label: r.label }))}
        />
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <DateRangePicker
          className="w-[16rem]"
          aria-label="Date range"
          from={fromDate}
          to={toDate}
          onValueChange={(range) => {
            setFromDate(range.from);
            setToDate(range.to);
          }}
        />
        {report !== "top-diagnoses" && report !== "nps" && (
          <Select value={groupBy} onValueChange={setGroupBy}>
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">Day</SelectItem>
              <SelectItem value="week">Week</SelectItem>
              <SelectItem value="month">Month</SelectItem>
              {report !== "patient-growth" && (
                <SelectItem value="doctor">Doctor</SelectItem>
              )}
              {report === "revenue" && (
                <SelectItem value="service_type">Service type</SelectItem>
              )}
            </SelectContent>
          </Select>
        )}
      </div>

      {report === "revenue" && data?.totals && (
        <div className="mb-4 grid grid-cols-3 gap-3">
          {(
            [
              ["Today", data.totals.today],
              ["Week", data.totals.week],
              ["Month", data.totals.month],
            ] as const
          ).map(([label, amount]) => (
            <Card key={label}>
              <CardContent className="pt-5">
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="mt-1 text-lg font-semibold text-foreground">
                  PHP {amount}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {report === "nps" ? (
        <Card>
          <CardContent className="flex flex-col gap-3 pt-5">
            {npsLoading ? (
              <ReportsSkeleton />
            ) : npsError ? (
              <ErrorState onRetry={() => refetchNps()} className="py-8" />
            ) : (npsData?.series ?? []).length === 0 ? (
              <EmptyState
                heading="No NPS responses for this range"
                icon={BarChart3}
                description="Adjust the date range to see results."
                className="py-8"
              />
            ) : (
              <div className="flex flex-col divide-y divide-border text-sm">
                {npsData?.series.map((row) => (
                  <div
                    key={row.period}
                    className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
                  >
                    <span className="font-medium text-foreground">
                      {row.period}
                    </span>
                    <span className="text-muted-foreground">
                      {row.responded}/{row.sent} responded
                    </span>
                    <span className="text-muted-foreground">
                      {row.promoters} promoters · {row.passives} passive ·{" "}
                      {row.detractors} detractors
                    </span>
                    <span className="font-semibold text-foreground">
                      NPS{" "}
                      {row.nps_score !== null ? row.nps_score.toFixed(0) : "—"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="flex flex-col gap-3 pt-5">
            {isLoading ? (
              <ReportsSkeleton />
            ) : isError ? (
              <ErrorState onRetry={() => refetch()} className="py-8" />
            ) : series.length === 0 ? (
              <EmptyState
                heading="No data for this range"
                icon={BarChart3}
                description="Adjust the date range or grouping to see results."
                className="py-8"
              />
            ) : (
              series.map((row, idx) => {
                const label = String(
                  row.period ??
                    row.doctor_name ??
                    row.doctor_id ??
                    row.service_type ??
                    row.diagnosis ??
                    idx,
                );
                let value = 0;
                if (report === "appointments") value = Number(row.booked ?? 0);
                else if (report === "revenue") value = Number(row.amount ?? 0);
                else if (report === "patient-growth")
                  value =
                    Number(row.new_patients ?? 0) +
                    Number(row.returning_patients ?? 0);
                else value = Number(row.visit_count ?? 0);
                const bar = (
                  <BarRow
                    key={`${label}-${idx}`}
                    label={label}
                    value={value}
                    max={maxValue}
                  />
                );
                if (report === "appointments") {
                  const period =
                    typeof row.period === "string" ? row.period : undefined;
                  return (
                    <Link
                      key={`${label}-${idx}`}
                      to="/dashboard/appointments"
                      search={{
                        from: period ?? fromDate,
                        to: period ?? toDate,
                        doctorId: row.doctor_id
                          ? String(row.doctor_id)
                          : undefined,
                      }}
                      className="block cursor-pointer rounded-md hover:bg-muted/50 native-press"
                    >
                      {bar}
                    </Link>
                  );
                }
                if (report === "revenue") {
                  return (
                    <Link
                      key={`${label}-${idx}`}
                      to="/dashboard/billing/invoices"
                      search={{ from: fromDate, to: toDate }}
                      className="block cursor-pointer rounded-md hover:bg-muted/50 native-press"
                    >
                      {bar}
                    </Link>
                  );
                }
                return bar;
              })
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
