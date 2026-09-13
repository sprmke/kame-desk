import { Link, Outlet, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { clearAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";

export function PlatformShell() {
  const navigate = useNavigate();
  const { data: me, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => api.me(),
  });

  if (isLoading) {
    return <div className="p-6 text-sm text-muted-foreground">Loading</div>;
  }
  if (!me?.is_platform_admin) {
    return (
      <div className="mx-auto max-w-lg p-6">
        <p className="text-sm text-foreground">Platform admin only.</p>
        <Button className="mt-4" onClick={() => navigate({ to: "/dashboard" })}>
          Back
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
        <span className="font-semibold text-foreground">Platform</span>
        <nav className="flex flex-wrap gap-3 text-sm">
          <Link to="/platform" className="text-primary hover:underline">
            Tenants
          </Link>
          <Link to="/platform/flags" className="text-primary hover:underline">
            Flags
          </Link>
          <Link to="/platform/metrics" className="text-primary hover:underline">
            Metrics
          </Link>
        </nav>
        <Button
          variant="ghost"
          size="sm"
          className="ml-auto"
          onClick={() => {
            clearAuth();
            navigate({ to: "/login" });
          }}
        >
          Sign out
        </Button>
      </header>
      <main className="p-4 sm:p-6">
        <Outlet />
      </main>
    </div>
  );
}
