import type { ReactNode } from "react";
import { ForbiddenPage } from "@/components/layout/ForbiddenPage";
import { useSession } from "@/hooks/useSession";
import { isAuthenticated, shouldDeferAuthRedirect } from "@/lib/auth";
import type { Permission } from "@/lib/rbac";
import { Skeleton } from "@/components/ui/skeleton";

type Props = {
  permission: Permission | Permission[];
  children: ReactNode;
};

export function RequirePermission({ permission, children }: Props) {
  const { isLoading, isError, user, can, canAny } = useSession();

  // The session query is disabled until the clinic id is readable from
  // localStorage, and `isLoading` is false while it is disabled. Without the
  // extra checks a signed-in user sees "Access denied" for a beat on every
  // cold load, before permissions arrive.
  const resolvingSession =
    shouldDeferAuthRedirect() ||
    isLoading ||
    (isAuthenticated() && !user && !isError);

  if (resolvingSession) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  const allowed = Array.isArray(permission)
    ? canAny(permission)
    : can(permission);

  if (!allowed) return <ForbiddenPage />;

  return children;
}
