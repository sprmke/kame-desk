import { Outlet } from "@tanstack/react-router";
import { SectionHubShell } from "@/components/layout/SectionHubShell";
import type { SectionHub } from "@/components/layout/nav-config";

/** Route-level wrapper for sections where every child route is a hub tab. */
export function SectionHubLayout({ hub }: { hub: SectionHub }) {
  return (
    <SectionHubShell hub={hub}>
      <Outlet />
    </SectionHubShell>
  );
}
