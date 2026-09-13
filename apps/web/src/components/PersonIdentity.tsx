import { cn } from "@/lib/utils";

const IDENTITY_BG = [
  "bg-[color:var(--identity-0)] text-foreground",
  "bg-[color:var(--identity-1)] text-foreground",
  "bg-[color:var(--identity-2)] text-foreground",
  "bg-[color:var(--identity-3)] text-foreground",
] as const;

function initialsFrom(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0] ?? ""}${parts[parts.length - 1]![0] ?? ""}`.toUpperCase();
}

function paletteIndex(seed: string) {
  let h = 0;
  for (let i = 0; i < seed.length; i += 1)
    h = (h + seed.charCodeAt(i) * (i + 1)) % 2147483647;
  return Math.abs(h) % IDENTITY_BG.length;
}

export function InitialsAvatar({
  name,
  seed,
  className,
}: {
  name: string;
  seed?: string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-medium",
        IDENTITY_BG[paletteIndex(seed ?? name)],
        className,
      )}
      aria-hidden
    >
      {initialsFrom(name)}
    </span>
  );
}

export function PersonIdentity({
  name,
  patientNumber,
  detail,
  className,
}: {
  name: string;
  patientNumber?: string | null;
  detail?: string | null;
  className?: string;
}) {
  const secondary = [patientNumber ? `#${patientNumber}` : null, detail]
    .filter(Boolean)
    .join(" · ");
  return (
    <div className={cn("flex min-w-0 items-center gap-2", className)}>
      <InitialsAvatar name={name} seed={patientNumber ?? name} />
      <div className="min-w-0">
        <p className="font-medium text-foreground" translate="no">
          {name}
        </p>
        {secondary ? (
          <p className="text-xs text-muted-foreground">
            {patientNumber ? (
              <span translate="no">#{patientNumber}</span>
            ) : null}
            {patientNumber && detail ? " · " : null}
            {detail}
          </p>
        ) : null}
      </div>
    </div>
  );
}
