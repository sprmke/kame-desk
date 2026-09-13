import { Check, type LucideIcon } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

export type StepperStep = {
  id: string;
  label: string;
  icon?: LucideIcon;
};

function trackInset(stepCount: number): string {
  return `calc(100% / ${stepCount * 2})`;
}

function StepTrack({
  stepCount,
  activeIndex,
}: {
  stepCount: number;
  activeIndex: number;
}) {
  if (stepCount <= 1) return null;
  const progressPct = (activeIndex / (stepCount - 1)) * 100;

  return (
    <div
      className="pointer-events-none absolute top-[1.125rem] h-0.5 -translate-y-1/2"
      style={{ left: trackInset(stepCount), right: trackInset(stepCount) }}
      aria-hidden
    >
      <div className="absolute inset-0 rounded-full bg-border" />
      <div
        className="absolute inset-y-0 left-0 rounded-full bg-primary transition-[width] duration-150 ease-theme motion-reduce:transition-none"
        style={{ width: `${progressPct}%` }}
      />
    </div>
  );
}

function StepNode({
  step,
  index,
  activeIndex,
}: {
  step: StepperStep;
  index: number;
  activeIndex: number;
}) {
  const done = index < activeIndex;
  const current = index === activeIndex;
  const upcoming = !done && !current;
  const Icon = step.icon;

  return (
    <li className="relative z-10 flex min-w-0 flex-1 flex-col items-center">
      <span
        className={cn(
          "flex size-9 shrink-0 items-center justify-center rounded-full border-2 bg-background transition-colors duration-150 ease-theme",
          done && "border-primary bg-primary text-primary-foreground",
          current && "border-primary text-primary shadow-theme-xs",
          upcoming && "border-border text-muted-foreground",
        )}
        aria-current={current ? "step" : undefined}
      >
        {done ? (
          <Check className="size-4" strokeWidth={2.5} aria-hidden />
        ) : Icon ? (
          <Icon
            className="size-4"
            strokeWidth={current ? 2.25 : 2}
            aria-hidden
          />
        ) : (
          <span className="text-xs font-semibold">{index + 1}</span>
        )}
      </span>
      <p
        className={cn(
          "mt-2.5 max-w-full truncate px-0.5 text-center text-xs leading-tight",
          current && "font-semibold text-foreground",
          done && !current && "font-medium text-foreground",
          upcoming && "font-normal text-muted-foreground",
        )}
      >
        {step.label}
      </p>
    </li>
  );
}

export function Stepper({
  steps,
  activeId,
  className,
}: {
  steps: StepperStep[];
  activeId: string;
  className?: string;
}) {
  const activeIndex = Math.max(
    0,
    steps.findIndex((step) => step.id === activeId),
  );
  const progressPct =
    steps.length <= 1
      ? 100
      : Math.round((activeIndex / (steps.length - 1)) * 100);
  const current = steps[activeIndex] ?? steps[0];
  const displayIndex = activeIndex + 1;

  return (
    <nav aria-label="Steps" className={cn("w-full", className)}>
      <div className="space-y-2.5 sm:hidden">
        <div className="flex items-baseline justify-between gap-3">
          <p className="text-sm font-semibold tracking-tight text-foreground">
            {current?.label ?? "Step"}
          </p>
          <p className="text-xs tabular-nums text-muted-foreground">
            {displayIndex} / {steps.length}
          </p>
        </div>
        <Progress
          value={progressPct}
          aria-valuetext={`Step ${displayIndex} of ${steps.length}`}
        />
      </div>

      <ol className="relative mx-auto hidden w-full sm:flex">
        <StepTrack stepCount={steps.length} activeIndex={activeIndex} />
        {steps.map((step, index) => (
          <StepNode
            key={step.id}
            step={step}
            index={index}
            activeIndex={activeIndex}
          />
        ))}
      </ol>
    </nav>
  );
}

/** Compact segmented bar for short wizards (import, generate). */
export function SegmentedProgress({
  labels,
  currentIndex,
  disabled,
}: {
  labels: readonly string[];
  currentIndex: number;
  disabled?: boolean;
}) {
  const current = labels[currentIndex] ?? "";

  return (
    <div
      className={cn(
        "flex items-center gap-2",
        disabled && "pointer-events-none opacity-60",
      )}
    >
      <div
        className="flex flex-1 items-center gap-1"
        role="progressbar"
        aria-valuemin={1}
        aria-valuemax={labels.length}
        aria-valuenow={currentIndex + 1}
        aria-valuetext={`Step ${currentIndex + 1} of ${labels.length}: ${current}`}
      >
        {labels.map((label, index) => (
          <span
            key={label}
            className={cn(
              "h-1.5 flex-1 rounded-full transition-colors duration-150 ease-theme",
              index <= currentIndex ? "bg-primary" : "bg-muted",
            )}
            aria-hidden
          />
        ))}
      </div>
      <span
        className="shrink-0 text-xs font-medium tabular-nums text-muted-foreground"
        aria-hidden
      >
        {currentIndex + 1}/{labels.length}
      </span>
    </div>
  );
}
