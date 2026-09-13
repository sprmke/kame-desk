import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";

function Slider({
  className,
  ...props
}: React.ComponentProps<typeof SliderPrimitive.Root>) {
  return (
    <SliderPrimitive.Root
      data-slot="slider"
      className={cn(
        "relative flex w-full touch-manipulation select-none items-center",
        className,
      )}
      {...props}
    >
      <SliderPrimitive.Track
        data-slot="slider-track"
        className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-muted"
      >
        <SliderPrimitive.Range
          data-slot="slider-range"
          className="absolute h-full bg-primary"
        />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb
        data-slot="slider-thumb"
        className="block size-3.5 cursor-pointer rounded-full border border-primary/20 bg-primary shadow-sm [@media(hover:hover)_and_(pointer:fine)]:hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
      />
    </SliderPrimitive.Root>
  );
}

type NumberSliderProps = {
  label?: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  id?: string;
  className?: string;
};

function NumberSlider({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  unit = "",
  id,
  className,
}: NumberSliderProps) {
  return (
    <div className={cn("min-w-0 space-y-2", className)}>
      {label ? (
        <div className="flex items-center justify-between gap-2">
          <label htmlFor={id} className="text-xs text-muted-foreground">
            {label}
          </label>
          <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
            {value}
            {unit}
          </span>
        </div>
      ) : null}
      <Slider
        id={id}
        min={min}
        max={max}
        step={step}
        value={[value]}
        onValueChange={([next]) => onChange(next)}
        aria-label={label}
      />
    </div>
  );
}

export { Slider, NumberSlider };
