import { Outlet } from "@tanstack/react-router";
import { SectionHubShell } from "@/components/layout/SectionHubShell";
import { RequirePermission } from "@/components/layout/RequirePermission";
import type { SectionHub } from "@/components/layout/nav-config";
import type { Permission } from "@/lib/rbac";

/** Route-level wrapper for sections where every child route is a hub tab. */
export function SectionHubLayout({
  hub,
  permission,
}: {
  hub: SectionHub;
  permission: Permission | Permission[];
}) {
  return (
    <SectionHubShell hub={hub}>
      <RequirePermission permission={permission}>
        <Outlet />
      </RequirePermission>
    </SectionHubShell>
  );
}
