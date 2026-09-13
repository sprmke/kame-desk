import { useQuery } from "@tanstack/react-query";
import { api, type SessionUser } from "@/lib/apiClient";
import { useActiveClinicId } from "@/hooks/useActiveClinicId";
import { can, canAny, type ClinicRole, type Permission } from "@/lib/rbac";

export function useSession() {
  const clinicId = useActiveClinicId();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["me", clinicId],
    queryFn: () => api.me(),
    enabled: Boolean(clinicId),
  });

  const role = (data?.active_clinic?.role ?? undefined) as
    ClinicRole | undefined;

  return {
    user: data,
    clinicId: clinicId ?? data?.active_clinic?.id,
    clinicName: data?.active_clinic?.name,
    role,
    permissions: data?.permissions ?? [],
    isPlatformAdmin: data?.is_platform_admin ?? false,
    memberships: data?.memberships?.filter((m) => m.is_active) ?? [],
    organizations: data?.organizations ?? [],
    isLoading,
    isError,
    error,
    refetch,
    can: (permission: Permission) => can(data?.permissions, permission),
    canAny: (permissions: Permission[]) =>
      canAny(data?.permissions, permissions),
  };
}

export type Session = ReturnType<typeof useSession>;
