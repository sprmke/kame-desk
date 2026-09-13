import { ClientOnly } from "@tanstack/react-router";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";
import { useTheme } from "@/components/theme/ThemeProvider";

type Point = { date: string; booked: number; completed: number };

function formatDay(iso: string) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function AppointmentsTrendChart({
  points,
  height = 288,
}: {
  points: Point[];
  height?: number;
}) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  const options: ApexOptions = {
    chart: {
      type: "area",
      toolbar: { show: false },
      fontFamily: "var(--font-sans)",
      sparkline: { enabled: false },
      background: "transparent",
      foreColor: isDark ? "#98a2b3" : "#667085",
      parentHeightOffset: 0,
      offsetY: 0,
    },
    colors: ["#465fff", "#12b76a"],
    dataLabels: { enabled: false },
    stroke: { curve: "smooth", width: 2 },
    fill: { type: "solid", opacity: [0.1, 0.04] },
    grid: {
      borderColor: "var(--border)",
      strokeDashArray: 4,
      padding: { top: 8, right: 8, bottom: 0, left: 4 },
      yaxis: { lines: { show: true } },
    },
    legend: {
      show: true,
      position: "top",
      horizontalAlign: "left",
      fontSize: "12px",
      height: 32,
      offsetY: 0,
      itemMargin: { horizontal: 12, vertical: 0 },
      labels: { colors: "var(--muted-foreground)" },
    },
    xaxis: {
      categories: points.map((p) => formatDay(p.date)),
      tickAmount: 7,
      axisBorder: { show: false },
      axisTicks: { show: false },
      labels: {
        rotate: 0,
        rotateAlways: false,
        hideOverlappingLabels: true,
        style: { colors: "var(--muted-foreground)" },
        offsetY: -2,
      },
    },
    yaxis: {
      labels: { style: { colors: "var(--muted-foreground)" }, offsetX: -4 },
      min: 0,
      forceNiceScale: true,
    },
    tooltip: { theme: isDark ? "dark" : "light" },
    responsive: [
      {
        breakpoint: 640,
        options: {
          legend: { height: 28, itemMargin: { horizontal: 8, vertical: 0 } },
          xaxis: {
            tickAmount: 4,
            labels: {
              rotate: 0,
              rotateAlways: false,
              hideOverlappingLabels: true,
            },
          },
          yaxis: { tickAmount: 4 },
        },
      },
    ],
  };

  const series = [
    { name: "Booked", data: points.map((p) => p.booked) },
    { name: "Completed", data: points.map((p) => p.completed) },
  ];
  const bookedTotal = points.reduce((sum, point) => sum + point.booked, 0);
  const completedTotal = points.reduce(
    (sum, point) => sum + point.completed,
    0,
  );

  return (
    <figure className="h-full w-full">
      <ClientOnly
        fallback={<div className="h-full w-full" style={{ height }} />}
      >
        <Chart
          key={resolvedTheme}
          options={options}
          series={series}
          type="area"
          height={height}
          width="100%"
        />
      </ClientOnly>
      <figcaption className="sr-only">
        Appointments over the last 14 days: {bookedTotal} booked and{" "}
        {completedTotal} completed.
      </figcaption>
    </figure>
  );
}
