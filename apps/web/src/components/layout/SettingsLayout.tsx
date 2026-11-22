import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { PageContainer } from "@/components/layout/PageContainer";
import { filterSettingsGroups } from "@/components/layout/settings-config";
import { RequirePermission } from "@/components/layout/RequirePermission";
import { useSession } from "@/hooks/useSession";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

function isActive(pathname: string, to: string) {
  return pathname === to || pathname.startsWith(`${to}/`);
}

export function SettingsLayout() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { can, isLoading } = useSession();
  const groups = filterSettingsGroups(can);

  return (
    <PageContainer>
      <div className="flex flex-col gap-6 lg:flex-row lg:gap-8">
        <nav className="flex shrink-0 flex-row gap-4 overflow-x-auto lg:w-52 lg:flex-col lg:gap-6">
          {isLoading && groups.length === 0
            ? [2, 6, 2, 2, 1].map((count, groupIndex) => (
                <div key={groupIndex} className="min-w-[140px]">
                  <Skeleton className="mb-2 ml-2 h-3 w-16" />
                  <div className="flex flex-col gap-0.5">
                    {Array.from({ length: count }).map((_, itemIndex) => (
                      <div
                        key={itemIndex}
                        className="flex h-9 items-center gap-2 px-2"
                      >
                        <Skeleton className="size-4 shrink-0 rounded" />
                        <Skeleton className="h-3.5 w-20 max-w-full" />
                      </div>
                    ))}
                  </div>
                </div>
              ))
            : groups.map((group) => (
                <div key={group.label} className="min-w-[140px]">
                  <p className="mb-1.5 px-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    {group.label}
                  </p>
                  <div className="flex flex-col gap-0.5">
                    {group.items.map((item) => {
                      const Icon = item.icon;
                      const active = isActive(pathname, item.to);
                      return (
                        <Link
                          key={item.to}
                          to={item.to}
                          className={cn(
                            "flex min-h-9 items-center gap-2 rounded-lg px-2 text-sm font-medium transition-colors duration-150 ease-theme",
                            active
                              ? "bg-secondary text-foreground"
                              : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
                          )}
                        >
                          <Icon className="size-4 shrink-0" />
                          <span className="truncate">{item.label}</span>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}
        </nav>
        <div className="min-w-0 flex-1">
          <RequirePermission
            permission={[
              "settings:account",
              "settings:doctor",
              "settings:clinic",
              "settings:team",
              "settings:services",
              "settings:notifications",
              "settings:assistant",
              "settings:templates",
              "settings:plan",
            ]}
          >
            <Outlet />
          </RequirePermission>
        </div>
      </div>
    </PageContainer>
  );
}
