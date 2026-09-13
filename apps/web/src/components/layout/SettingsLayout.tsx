import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { PageContainer } from "@/components/layout/PageContainer";
import { filterSettingsGroups } from "@/components/layout/settings-config";
import { useSession } from "@/hooks/useSession";
import { cn } from "@/lib/utils";

function isActive(pathname: string, to: string) {
  return pathname === to || pathname.startsWith(`${to}/`);
}

export function SettingsLayout() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { can } = useSession();
  const groups = filterSettingsGroups(can);

  return (
    <PageContainer>
      <div className="flex flex-col gap-6 lg:flex-row lg:gap-8">
        <nav className="flex shrink-0 flex-row gap-4 overflow-x-auto lg:w-52 lg:flex-col lg:gap-6">
          {groups.map((group) => (
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
          <Outlet />
        </div>
      </div>
    </PageContainer>
  );
}
