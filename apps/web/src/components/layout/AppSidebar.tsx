import { Link, useRouterState } from "@tanstack/react-router";
import { PanelLeftClose } from "lucide-react";
import { ProductMark } from "@/components/brand/ProductMark";
import { cn } from "@/lib/utils";
import {
  filterNavItems,
  mainNavItems,
  type NavLeaf,
} from "@/components/layout/nav-config";
import { useSidebar } from "@/components/layout/SidebarContext";
import { WorkspaceSwitcher } from "@/components/layout/WorkspaceSwitcher";
import { useSession } from "@/hooks/useSession";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

function isActive(pathname: string, to: string) {
  if (to === "/dashboard") return pathname === "/dashboard";
  return pathname === to || pathname.startsWith(`${to}/`);
}

function SidebarHeader({
  collapsed,
  toggle,
}: {
  collapsed: boolean;
  toggle: () => void;
}) {
  if (collapsed) {
    // Collapsed rail has room for one control: the mark doubles as the expander.
    return (
      <div className="flex h-14 shrink-0 items-center justify-center px-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={toggle}
              aria-label="Expand sidebar"
              className="group relative flex size-11 items-center justify-center rounded-xl transition-colors duration-150 ease-theme hover:bg-sidebar-accent/60"
            >
              <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <ProductMark className="size-5" />
              </span>
            </button>
          </TooltipTrigger>
          <TooltipContent side="right">Expand sidebar</TooltipContent>
        </Tooltip>
      </div>
    );
  }

  return (
    <div className="flex h-14 shrink-0 items-center gap-1 px-3">
      <Link
        to="/dashboard"
        className="flex min-w-0 flex-1 items-center gap-2.5 rounded-lg px-1 py-1"
      >
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <ProductMark className="size-5" />
        </span>
        <span className="truncate text-base font-semibold text-foreground">
          DoctorDesk
        </span>
      </Link>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            onClick={toggle}
            aria-label="Collapse sidebar"
            className="flex size-11 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors duration-150 ease-theme hover:bg-sidebar-accent/60 hover:text-foreground"
          >
            <PanelLeftClose className="size-4" aria-hidden />
          </button>
        </TooltipTrigger>
        <TooltipContent side="right">Collapse sidebar</TooltipContent>
      </Tooltip>
    </div>
  );
}

function NavLink({
  item,
  active,
  collapsed,
}: {
  item: NavLeaf;
  active: boolean;
  collapsed: boolean;
}) {
  const Icon = item.icon;
  const link = (
    <Link
      to={item.to}
      aria-label={collapsed ? item.label : undefined}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-150 ease-theme",
        collapsed && "justify-center px-0",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
      )}
    >
      <Icon
        className="size-[18px] shrink-0"
        absoluteStrokeWidth
        strokeWidth={1.75}
        aria-hidden
      />
      {!collapsed && <span className="truncate">{item.label}</span>}
    </Link>
  );

  if (!collapsed) return link;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="block">{link}</span>
      </TooltipTrigger>
      <TooltipContent side="right">{item.label}</TooltipContent>
    </Tooltip>
  );
}

function SidebarBody({ collapsed }: { collapsed: boolean }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { can } = useSession();
  const items = filterNavItems(mainNavItems, can);

  return (
    <nav className="flex-1 overflow-y-auto px-3 pb-4 pt-2">
      <div className="flex flex-col gap-0.5">
        {items.map((item) => (
          <NavLink
            key={item.to}
            item={item}
            active={isActive(pathname, item.to)}
            collapsed={collapsed}
          />
        ))}
      </div>
    </nav>
  );
}

export function AppSidebar() {
  const { collapsed, toggle } = useSidebar();

  return (
    <aside
      className={cn(
        "hidden shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-150 ease-theme lg:flex",
        collapsed ? "w-[76px]" : "w-64",
      )}
    >
      <SidebarHeader collapsed={collapsed} toggle={toggle} />
      <WorkspaceSwitcher collapsed={collapsed} />
      <SidebarBody collapsed={collapsed} />
    </aside>
  );
}
