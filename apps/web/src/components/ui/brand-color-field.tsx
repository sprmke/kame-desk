import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export const DEFAULT_CLINIC_BRAND_COLOR = "#465fff";

const PRESETS = [
  { label: "Indigo", hex: "#465fff" },
  { label: "Blue", hex: "#3641f5" },
  { label: "Teal", hex: "#026aa2" },
  { label: "Green", hex: "#12b76a" },
  { label: "Navy", hex: "#252dae" },
  { label: "Slate", hex: "#475467" },
] as const;

const RAINBOW_SWATCH =
  "conic-gradient(from 180deg, #FB923C, #FBBF24, #A3E635, #34D399, #38BDF8, #6366F1, #E879F9, #FB7185, #FB923C)";

type BrandColorFieldProps = {
  id: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  resetValue?: string;
  label?: string;
};

export function BrandColorField({
  id,
  value,
  onChange,
  disabled = false,
  resetValue = DEFAULT_CLINIC_BRAND_COLOR,
  label = "Brand color",
}: BrandColorFieldProps) {
  const normalized = value.trim().toLowerCase();
  const isPreset = PRESETS.some((p) => p.hex.toLowerCase() === normalized);
  const isCustomSelected = Boolean(normalized) && !isPreset;
  const isAtReset = normalized === resetValue.toLowerCase();

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={`${id}-picker`}>{label}</Label>
      <div className="flex flex-wrap items-center gap-2">
        {PRESETS.map((preset) => {
          const selected = normalized === preset.hex.toLowerCase();
          return (
            <button
              key={preset.hex}
              type="button"
              disabled={disabled}
              onClick={() => onChange(preset.hex)}
              className={cn(
                "flex size-9 shrink-0 cursor-pointer items-center justify-center rounded-full border border-border shadow-sm transition-transform hover:scale-105 active:scale-95 disabled:pointer-events-none disabled:opacity-50",
                selected &&
                  "ring-2 ring-foreground ring-offset-2 ring-offset-background",
              )}
              style={{ backgroundColor: preset.hex }}
              aria-label={`Use ${preset.label}`}
              aria-pressed={selected}
            >
              {selected ? (
                <Check
                  className="size-3.5 text-white drop-shadow-sm"
                  aria-hidden
                />
              ) : null}
            </button>
          );
        })}
        <label
          htmlFor={`${id}-picker`}
          className={cn(
            "relative flex size-9 shrink-0 cursor-pointer items-center justify-center rounded-full border border-border shadow-sm",
            disabled && "pointer-events-none opacity-50",
            isCustomSelected &&
              "ring-2 ring-foreground ring-offset-2 ring-offset-background",
          )}
          style={{ background: RAINBOW_SWATCH }}
        >
          {isCustomSelected ? (
            <Check className="size-3.5 text-white drop-shadow-sm" aria-hidden />
          ) : null}
          <input
            id={`${id}-picker`}
            type="color"
            value={value || DEFAULT_CLINIC_BRAND_COLOR}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="absolute inset-0 size-full cursor-pointer opacity-0"
            aria-label="Pick custom color"
          />
        </label>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled || isAtReset}
          onClick={() => onChange(resetValue)}
        >
          Reset
        </Button>
      </div>
    </div>
  );
}
