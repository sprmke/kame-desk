import { Link } from "@tanstack/react-router";
import { ProductMark } from "@/components/brand/ProductMark";
import { ThemeToggle } from "@/components/theme/ThemeToggle";

export function AuthLayout({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen lg:grid lg:grid-cols-[20rem_minmax(0,1fr)]">
      <aside className="hidden flex-col justify-between bg-primary px-8 py-10 text-primary-foreground lg:flex">
        <Link to="/" className="flex items-center gap-2.5">
          <ProductMark className="size-7" />
          <span className="text-base font-semibold">DoctorDesk</span>
        </Link>
      </aside>
      <div className="flex min-h-screen flex-col px-6 py-10">
        <div className="mb-10 flex items-center justify-between gap-3 lg:justify-end">
          <Link to="/" className="flex items-center gap-2 lg:hidden">
            <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ProductMark className="size-5" />
            </span>
            <span className="text-base font-semibold text-foreground">
              DoctorDesk
            </span>
          </Link>
          <ThemeToggle />
        </div>
        <div className="mx-auto w-full max-w-sm flex-1">
          <h1 className="mb-6 text-lg font-semibold text-foreground">
            {title}
          </h1>
          {children}
        </div>
      </div>
    </div>
  );
}
