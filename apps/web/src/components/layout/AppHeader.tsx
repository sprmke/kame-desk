import { useNavigate } from "@tanstack/react-router";
import {
  LogOut,
  Monitor,
  Moon,
  Search,
  Settings,
  ShieldCheck,
  Sun,
} from "lucide-react";
import { api } from "@/lib/apiClient";
import { clearAuth, getRefreshToken } from "@/lib/auth";
import { ROLE_LABELS } from "@/lib/rbac";
import { useSession } from "@/hooks/useSession";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTheme } from "@/components/theme/ThemeProvider";
import type { ThemePreference } from "@/lib/theme/preferences";
import { NotificationBell } from "@/features/notifications/components/NotificationBell";

const THEME_OPTIONS: Array<{
  value: ThemePreference;
  label: string;
  Icon: typeof Sun;
}> = [
  { value: "light", label: "Light", Icon: Sun },
  { value: "dark", label: "Dark", Icon: Moon },
  { value: "system", label: "System", Icon: Monitor },
];

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function AppHeader({ onOpenSearch }: { onOpenSearch: () => void }) {
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();
  const { user, role, clinicName, isPlatformAdmin, canAny } = useSession();
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

  async function handleLogout() {
    const refreshToken = getRefreshToken();
    try {
      if (refreshToken) await api.logout(refreshToken);
    } catch {
      // Best-effort: clear local session regardless of server response.
    }
    clearAuth();
    navigate({ to: "/login" });
  }

  return (
    <header className="flex min-h-16 shrink-0 items-center gap-3 border-b border-border bg-card px-4 sm:px-6 pt-[env(safe-area-inset-top)]">
      <button
        type="button"
        onClick={onOpenSearch}
        className="flex min-h-11 w-full max-w-xs items-center gap-2 rounded-lg border border-input bg-secondary/50 px-3 text-sm text-muted-foreground transition-colors hover:bg-secondary sm:max-w-sm"
      >
        <Search className="size-4" />
        <span className="flex-1 text-left">Search patients, appointments…</span>
        <kbd className="hidden rounded border border-border bg-card px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground sm:inline">
          ⌘K
        </kbd>
      </button>

      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        <NotificationBell />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label="Account menu"
              className="flex size-11 items-center justify-center rounded-full transition-colors hover:bg-secondary"
            >
              <Avatar>
                <AvatarFallback>
                  {initials(user?.full_name ?? "?")}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel className="flex flex-col gap-0.5 px-2 py-1.5">
              <span className="truncate text-sm font-medium text-foreground">
                {user?.full_name}
              </span>
              <span className="truncate text-xs text-muted-foreground">
                {user?.email}
              </span>
              {role && clinicName ? (
                <span className="truncate text-xs text-muted-foreground">
                  {ROLE_LABELS[role]} · {clinicName}
                </span>
              ) : null}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {hasSettings ? (
              <DropdownMenuItem
                onSelect={() => navigate({ to: "/dashboard/settings/account" })}
              >
                <Settings />
                Settings
              </DropdownMenuItem>
            ) : null}
            {isPlatformAdmin ? (
              <DropdownMenuItem onSelect={() => navigate({ to: "/platform" })}>
                <ShieldCheck />
                Platform
              </DropdownMenuItem>
            ) : null}
            {hasSettings || isPlatformAdmin ? <DropdownMenuSeparator /> : null}
            <DropdownMenuLabel>Theme</DropdownMenuLabel>
            <DropdownMenuRadioGroup
              value={theme}
              onValueChange={(next) => setTheme(next as ThemePreference)}
            >
              {THEME_OPTIONS.map(({ value, label, Icon }) => (
                <DropdownMenuRadioItem
                  key={value}
                  value={value}
                  // Keep the menu open so the change is visible in place.
                  onSelect={(event) => event.preventDefault()}
                >
                  <Icon className="size-4 text-muted-foreground" aria-hidden />
                  {label}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" onSelect={handleLogout}>
              <LogOut />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
