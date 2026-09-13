import { useMemo } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { ChevronsUpDown } from "lucide-react";
import { setActiveClinic } from "@/lib/auth";
import { defaultLandingPath, ROLE_LABELS, type ClinicRole } from "@/lib/rbac";
import { useActiveClinicId } from "@/hooks/useActiveClinicId";
import { useSession } from "@/hooks/useSession";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

type Props = {
  collapsed?: boolean;
};

type Membership = ReturnType<typeof useSession>["memberships"][number];

function clinicLabel(membership: Membership, memberships: Membership[]) {
  const duplicateName = memberships.some(
    (other) =>
      other.clinic_id !== membership.clinic_id &&
      other.clinic_name === membership.clinic_name,
  );
  if (duplicateName && membership.organization_name) {
    return `${membership.clinic_name} (${membership.organization_name})`;
  }
  return membership.clinic_name;
}

export function WorkspaceSwitcher({ collapsed }: Props) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const activeClinicId = useActiveClinicId();
  const { clinicName, role, memberships } = useSession();

  const labelsByClinicId = useMemo(() => {
    const labels = new Map<string, string>();
    for (const membership of memberships) {
      labels.set(membership.clinic_id, clinicLabel(membership, memberships));
    }
    return labels;
  }, [memberships]);

  if (!activeClinicId) return null;

  function switchClinic(nextId: string) {
    if (nextId === activeClinicId) return;
    setActiveClinic(nextId);
    qc.clear();
    const nextRole = memberships.find((m) => m.clinic_id === nextId)?.role as
      ClinicRole | undefined;
    void navigate({ to: defaultLandingPath(nextRole), replace: true });
  }

  const roleLabel = role ? ROLE_LABELS[role] : "";

  if (memberships.length <= 1) {
    if (collapsed) return null;
    return (
      <div className="border-b border-sidebar-border px-4 py-3">
        <p className="truncate text-sm font-medium text-foreground">
          {clinicName}
        </p>
        {roleLabel ? (
          <p className="text-xs text-muted-foreground">{roleLabel}</p>
        ) : null}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "border-b border-sidebar-border px-3 py-3",
        collapsed && "px-2",
      )}
    >
      <Select value={activeClinicId} onValueChange={switchClinic}>
        <SelectTrigger
          size="sm"
          className={cn(
            "h-auto min-h-9 w-full min-w-0 border-sidebar-border bg-sidebar py-2",
            "[&_[data-slot=select-value]]:line-clamp-1 [&_[data-slot=select-value]]:truncate",
            collapsed && "justify-center px-0",
          )}
        >
          {collapsed ? (
            <ChevronsUpDown className="size-4 shrink-0" />
          ) : (
            <SelectValue placeholder="Clinic" />
          )}
        </SelectTrigger>
        <SelectContent className="min-w-[var(--radix-select-trigger-width)]">
          {memberships.map((membership) => (
            <SelectItem
              key={membership.clinic_id}
              value={membership.clinic_id}
              className="min-w-0"
            >
              <span className="truncate">
                {labelsByClinicId.get(membership.clinic_id) ??
                  membership.clinic_name}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {!collapsed && roleLabel ? (
        <p className="mt-1.5 px-1 text-xs text-muted-foreground">{roleLabel}</p>
      ) : null}
    </div>
  );
}
