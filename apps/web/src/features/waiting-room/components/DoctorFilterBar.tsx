import { cn } from "@/lib/utils";

type DoctorOption = {
  id: string;
  name: string;
  count: number;
};

type Props = {
  doctors: DoctorOption[];
  totalCount: number;
  value: string | "all";
  onChange: (value: string | "all") => void;
};

export function DoctorFilterBar({
  doctors,
  totalCount,
  value,
  onChange,
}: Props) {
  if (doctors.length <= 1) return null;

  return (
    <div
      className="flex gap-1.5 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      role="group"
      aria-label="Filter by doctor"
    >
      <FilterPill
        label="All"
        count={totalCount}
        active={value === "all"}
        onClick={() => onChange("all")}
      />
      {doctors.map((doctor) => (
        <FilterPill
          key={doctor.id}
          label={doctor.name}
          count={doctor.count}
          active={value === doctor.id}
          onClick={() => onChange(doctor.id)}
        />
      ))}
    </div>
  );
}

function FilterPill({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "inline-flex h-9 shrink-0 items-center gap-1.5 rounded-full border px-3 text-sm font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        active
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border bg-card text-foreground hover:bg-secondary",
      )}
    >
      <span className="max-w-[10rem] truncate">{label}</span>
      <span
        className={cn(
          "tabular-nums text-xs",
          active ? "text-primary-foreground/80" : "text-muted-foreground",
        )}
      >
        {count}
      </span>
    </button>
  );
}
