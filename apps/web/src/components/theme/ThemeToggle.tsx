import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/components/theme/ThemeProvider";
import { cn } from "@/lib/utils";

type Props = {
  className?: string;
};

/** Compact toggle for auth, landing, onboarding, and the patient portal. Inside
 * the dashboard, theme lives in the account menu (`AppHeader`). */
export function ThemeToggle({ className }: Props) {
  const { toggleTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = mounted && resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      disabled={!mounted}
      className={cn(
        "relative inline-flex size-11 min-h-11 min-w-11 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground shadow-theme-xs",
        "transition-colors duration-150 ease-theme hover:bg-secondary hover:text-foreground",
        "focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:outline-none",
        className,
      )}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      <Sun
        className={cn(
          "size-4 transition-all duration-150 ease-theme",
          isDark ? "rotate-0 scale-100" : "rotate-90 scale-0",
        )}
        aria-hidden
      />
      <Moon
        className={cn(
          "absolute size-4 transition-all duration-150 ease-theme",
          isDark ? "rotate-90 scale-0" : "rotate-0 scale-100",
        )}
        aria-hidden
      />
    </button>
  );
}
