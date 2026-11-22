import { SectionHubShell } from "@/components/layout/SectionHubShell";
import { patientsHub } from "@/components/layout/nav-config";
import { RequirePermission } from "@/components/layout/RequirePermission";

export function PatientsHubShell({ children }: { children: React.ReactNode }) {
  return (
    <SectionHubShell hub={patientsHub}>
      <RequirePermission permission="patients:view">
        {children}
      </RequirePermission>
    </SectionHubShell>
  );
}
