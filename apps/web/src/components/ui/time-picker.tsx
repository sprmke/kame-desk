import * as React from "react";
import { Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

const DEFAULT_STEP_MINUTES = 15;

function formatTimeLabel(value: string): string {
  const [h, m] = value.split(":").map(Number);
  if (Number.isNaN(h) || Number.isNaN(m)) return value;
  const period = h >= 12 ? "PM" : "AM";
  const hour12 = h % 12 === 0 ? 12 : h % 12;
  return `${hour12}:${String(m).padStart(2, "0")} ${period}`;
}

function buildTimeOptions(stepMinutes: number, value?: string): string[] {
  const options: string[] = [];
  for (let minutes = 0; minutes < 24 * 60; minutes += stepMinutes) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    options.push(`${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`);
  }
  if (value && !options.includes(value)) {
    options.push(value);
    options.sort();
  }
  return options;
}

export type TimePickerProps = {
  id?: string;
  name?: string;
  value?: string;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  onValueChange?: (value: string) => void;
  onBlur?: React.FocusEventHandler<HTMLButtonElement>;
  disabled?: boolean;
  disabledTime?: (value: string) => boolean;
  placeholder?: string;
  className?: string;
  stepMinutes?: number;
  "aria-invalid"?: boolean;
  "aria-label"?: string;
};

function emitChange(
  onChange: TimePickerProps["onChange"],
  name: string | undefined,
  next: string,
) {
  onChange?.({
    target: { value: next, name: name ?? "" },
    currentTarget: { value: next, name: name ?? "" },
  } as React.ChangeEvent<HTMLInputElement>);
}

export const TimePicker = React.forwardRef<HTMLButtonElement, TimePickerProps>(
  function TimePicker(
    {
      id,
      name,
      value,
      onChange,
      onValueChange,
      onBlur,
      disabled,
      disabledTime,
      placeholder = "Pick a time",
      className,
      stepMinutes = DEFAULT_STEP_MINUTES,
      "aria-invalid": ariaInvalid,
      "aria-label": ariaLabel,
    },
    ref,
  ) {
    const [open, setOpen] = React.useState(false);
    const options = React.useMemo(
      () => buildTimeOptions(stepMinutes, value),
      [stepMinutes, value],
    );
    const selectedRef = React.useRef<HTMLButtonElement>(null);

    React.useEffect(() => {
      if (open) selectedRef.current?.scrollIntoView({ block: "center" });
    }, [open]);

    return (
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger
          ref={ref}
          id={id}
          name={name}
          type="button"
          disabled={disabled}
          aria-invalid={ariaInvalid}
          aria-label={ariaLabel}
          aria-haspopup="listbox"
          aria-expanded={open}
          onBlur={onBlur}
          className={cn(
            "flex h-10 w-full items-center rounded-lg border border-input bg-card px-3 text-left text-sm shadow-theme-xs transition-[color,background-color,border-color,box-shadow] duration-150 ease-theme",
            "hover:border-muted-foreground/40",
            "focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/20 focus-visible:outline-none",
            "disabled:cursor-not-allowed disabled:opacity-50",
            ariaInvalid && "border-destructive",
            value ? "text-foreground" : "text-muted-foreground",
            className,
          )}
        >
          <Clock
            className={cn(
              "mr-2 size-4 shrink-0",
              value ? "text-foreground" : "text-muted-foreground",
            )}
            aria-hidden
          />
          <span className="truncate">
            {value ? formatTimeLabel(value) : placeholder}
          </span>
        </PopoverTrigger>
        <PopoverContent
          className="max-h-64 w-40 overflow-y-auto p-1"
          align="start"
          role="listbox"
        >
          {options.map((option) => {
            const isSelected = option === value;
            const isDisabled = disabledTime?.(option) ?? false;
            return (
              <Button
                key={option}
                ref={isSelected ? selectedRef : undefined}
                type="button"
                variant={isSelected ? "secondary" : "ghost"}
                disabled={isDisabled}
                role="option"
                aria-selected={isSelected}
                className="w-full justify-start px-2 font-normal"
                onClick={() => {
                  emitChange(onChange, name, option);
                  onValueChange?.(option);
                  setOpen(false);
                }}
              >
                {formatTimeLabel(option)}
              </Button>
            );
          })}
        </PopoverContent>
      </Popover>
    );
  },
);
