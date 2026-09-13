import { cn } from "@/lib/utils";

export function formatPhp(amount: string | number | null | undefined): string {
  if (amount == null || amount === "") return "PHP 0";
  return `PHP ${amount}`;
}

export function Money({
  amount,
  className,
}: {
  amount: string | number | null | undefined;
  className?: string;
}) {
  return <span className={cn("dd-nums", className)}>{formatPhp(amount)}</span>;
}
