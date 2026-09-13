import { SectionHubShell } from "@/components/layout/SectionHubShell";
import { patientsHub } from "@/components/layout/nav-config";
import { RequirePermission } from "@/components/layout/RequirePermission";

export function PatientsHubShell({ children }: { children: React.ReactNode }) {
  return (
    <RequirePermission permission="patients:view">
      <SectionHubShell hub={patientsHub}>{children}</SectionHubShell>
    </RequirePermission>
  );
}
