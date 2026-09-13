import { cn } from "@/lib/utils";

export function Field({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="field"
      className={cn("flex flex-col gap-1.5", className)}
      {...props}
    />
  );
}

export function FieldError({
  id,
  children,
  className,
}: {
  id?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  if (!children) return null;
  return (
    <p
      id={id}
      role="alert"
      className={cn("text-xs font-medium text-destructive", className)}
    >
      {children}
    </p>
  );
}
