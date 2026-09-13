import { Link, useRouterState } from "@tanstack/react-router";
import type { SectionTab } from "@/components/layout/nav-config";
import type { Permission } from "@/lib/rbac";
import { SlidingActivePill } from "@/components/ui/sliding-active-pill";
import { useSlidingActivePill } from "@/hooks/useSlidingActivePill";
import { cn } from "@/lib/utils";

type Props = {
  tabs: SectionTab[];
  can?: (permission: Permission) => boolean;
  /** Section name, announced as the tab list's accessible label. */
  label?: string;
  className?: string;
};

function tabActive(pathname: string, to: string) {
  if (to.endsWith("/patients") || to === "/dashboard/appointments") {
    return pathname === to || pathname === `${to}/`;
  }
  return pathname === to || pathname.startsWith(`${to}/`);
}

export function SectionSubNav({ tabs, can, label, className }: Props) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const visible = tabs.filter(
    (tab) => !tab.permission || !can || can(tab.permission),
  );
  const activeKey =
    visible.find((tab) => tabActive(pathname, tab.to))?.to ??
    visible[0]?.to ??
    "";

  const { containerRef, setItemRef, bounds } = useSlidingActivePill(
    activeKey,
    visible.map((t) => t.to),
  );

  if (visible.length <= 1) return null;

  return (
    <nav
      ref={containerRef}
      className={cn(
        "relative inline-flex h-9 max-w-full items-stretch overflow-x-auto rounded-lg bg-muted p-0.5",
        className,
      )}
      aria-label={label ?? "Section"}
    >
      {bounds ? <SlidingActivePill bounds={bounds} /> : null}
      {visible.map((tab) => (
        <Link
          key={tab.to}
          to={tab.to}
          ref={setItemRef(tab.to)}
          className={cn(
            "relative z-10 inline-flex h-full items-center whitespace-nowrap rounded-md px-3 text-sm font-medium transition-colors duration-150 ease-theme",
            tabActive(pathname, tab.to)
              ? "text-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}
