import { cn } from "@/lib/utils";

type Props = {
  title: string;
  description?: string;
  leading?: React.ReactNode;
  actions?: React.ReactNode;
  /** Secondary navigation, rendered under the title and above page content. */
  subNav?: React.ReactNode;
  className?: string;
};

export function PageHeader({
  title,
  description,
  leading,
  actions,
  subNav,
  className,
}: Props) {
  return (
    <div className={cn("mb-4 sm:mb-6", className)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          {leading}
          <div className="min-w-0">
            <h1 className="text-xl font-semibold text-foreground sm:text-2xl">
              {title}
            </h1>
            {description && (
              <p className="mt-1 text-sm text-muted-foreground">
                {description}
              </p>
            )}
          </div>
        </div>
        {actions && (
          <div className="flex flex-wrap items-center gap-2">{actions}</div>
        )}
      </div>
      {subNav && <div className="mt-4">{subNav}</div>}
    </div>
  );
}
