import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { ProductMark } from "@/components/brand/ProductMark";
import { clearPatientAuth } from "@/lib/patientPortalAuth";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { key: "visits", label: "Visits", segment: "visits" },
  { key: "chart", label: "Chart", segment: "chart" },
  { key: "invoices", label: "Billing", segment: "invoices" },
  { key: "documents", label: "Documents", segment: "documents" },
] as const;

export function PatientPortalAppShell({
  slug,
  clinicName,
  patientName,
  children,
}: {
  slug: string;
  clinicName?: string;
  patientName?: string;
  children: React.ReactNode;
}) {
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2.5">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ProductMark className="size-4" />
            </span>
            <div className="leading-tight">
              <p className="text-sm font-semibold text-foreground">
                {clinicName ?? "Patient Portal"}
              </p>
              {patientName ? (
                <p className="text-xs text-muted-foreground">{patientName}</p>
              ) : null}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button
              type="button"
              className="min-h-11 rounded-md px-3 text-sm font-medium text-muted-foreground hover:text-foreground"
              onClick={() => {
                clearPatientAuth();
                navigate({
                  to: "/patient-portal/$slug/login",
                  params: { slug },
                });
              }}
            >
              Log out
            </button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-3xl gap-1 overflow-x-auto px-4 pb-2 sm:px-6">
          {NAV_ITEMS.map((item) => {
            const href = `/patient-portal/${slug}/${item.segment}`;
            const active = pathname === href;
            return (
              <Link
                key={item.key}
                to={href}
                className={cn(
                  "min-h-11 shrink-0 rounded-md px-3 py-2 text-sm font-medium",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6">{children}</main>
    </div>
  );
}
