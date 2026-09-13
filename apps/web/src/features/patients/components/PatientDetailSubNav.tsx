import { Link, useRouterState } from "@tanstack/react-router";
import type { PatientDetailSection } from "@/features/patients/pages/PatientDetailPage";
import { SlidingActivePill } from "@/components/ui/sliding-active-pill";
import { useSlidingActivePill } from "@/hooks/useSlidingActivePill";
import { cn } from "@/lib/utils";

const TABS: { label: string; section: PatientDetailSection; suffix: string }[] =
  [
    { label: "Overview", section: "overview", suffix: "" },
    { label: "Timeline", section: "timeline", suffix: "/timeline" },
    {
      label: "Prescriptions",
      section: "prescriptions",
      suffix: "/prescriptions",
    },
    { label: "Billing", section: "billing", suffix: "/billing" },
    { label: "Orders", section: "orders", suffix: "/orders" },
    { label: "Documents", section: "documents", suffix: "/documents" },
    { label: "Activity", section: "activity", suffix: "/activity" },
  ];

export function PatientDetailSubNav({ patientId }: { patientId: string }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const base = `/dashboard/patients/${patientId}`;
  const activeKey =
    TABS.find((tab) =>
      tab.section === "overview"
        ? pathname === base || pathname === `${base}/`
        : pathname.startsWith(`${base}${tab.suffix}`),
    )?.section ?? "overview";

  const { containerRef, setItemRef, bounds } = useSlidingActivePill(
    activeKey,
    TABS.map((t) => t.section),
  );

  return (
    <nav
      ref={containerRef}
      className="relative inline-flex h-9 max-w-full items-stretch overflow-x-auto rounded-lg bg-muted p-0.5"
      aria-label="Patient sections"
    >
      {bounds ? <SlidingActivePill bounds={bounds} /> : null}
      {TABS.map((tab) => {
        const to =
          tab.section === "overview"
            ? "/dashboard/patients/$patientId/"
            : `/dashboard/patients/$patientId${tab.suffix}`;
        const active = activeKey === tab.section;
        return (
          <Link
            key={tab.section}
            to={to}
            params={{ patientId }}
            ref={setItemRef(tab.section)}
            className={cn(
              "relative z-10 inline-flex h-full items-center whitespace-nowrap rounded-md px-3 text-sm font-medium transition-colors duration-150 ease-theme",
              active
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
