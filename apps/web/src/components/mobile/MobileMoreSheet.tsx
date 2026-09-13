import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { Settings } from "lucide-react";
import { moreNavItems, type NavLeaf } from "@/components/layout/nav-config";
import { useSession } from "@/hooks/useSession";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

function isActive(pathname: string, to: string) {
  if (to === "/dashboard") return pathname === "/dashboard";
  return pathname === to || pathname.startsWith(`${to}/`);
}

function MoreLink({
  item,
  active,
  onNavigate,
}: {
  item: NavLeaf;
  active: boolean;
  onNavigate: () => void;
}) {
  const Icon = item.icon;
  return (
    <Link
      to={item.to}
      onClick={onNavigate}
      className={cn(
        "flex min-h-[44px] items-center gap-3 rounded-lg px-3 text-sm font-medium native-press",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-foreground hover:bg-secondary",
      )}
    >
      <Icon className="size-[18px] shrink-0" />
      {item.label}
    </Link>
  );
}

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function MobileMoreSheet({ open, onOpenChange }: Props) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const navigate = useNavigate();
  const { can, canAny } = useSession();
  const items = moreNavItems(can);
  const hasSettings = canAny([
    "settings:account",
    "settings:doctor",
    "settings:clinic",
    "settings:team",
    "settings:services",
    "settings:notifications",
    "settings:assistant",
    "settings:templates",
    "settings:plan",
  ]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="gap-0 px-0">
        <SheetHeader className="px-4">
          <SheetTitle>More</SheetTitle>
        </SheetHeader>
        <nav className="max-h-[70dvh] overflow-y-auto px-3 pb-2">
          <div className="flex flex-col gap-0.5">
            {items.map((item) => (
              <MoreLink
                key={item.to}
                item={item}
                active={isActive(pathname, item.to)}
                onNavigate={() => onOpenChange(false)}
              />
            ))}
            {hasSettings ? (
              <button
                type="button"
                onClick={() => {
                  onOpenChange(false);
                  navigate({ to: "/dashboard/settings/account" });
                }}
                className="flex min-h-[44px] items-center gap-3 rounded-lg px-3 text-sm font-medium text-foreground native-press hover:bg-secondary"
              >
                <Settings className="size-[18px] shrink-0" />
                Settings
              </button>
            ) : null}
          </div>
        </nav>
      </SheetContent>
    </Sheet>
  );
}
