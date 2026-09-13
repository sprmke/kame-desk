import * as React from "react";
import { format, startOfDay } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";
import type { DateRange, Matcher } from "react-day-picker";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { parseIsoDate, toIsoDate } from "@/lib/isoDate";
import { useIsMobile } from "@/hooks/useMediaQuery";
import { cn } from "@/lib/utils";

const DISPLAY_FORMAT = "MMM d, yyyy";

export type DatePickerProps = {
  id?: string;
  name?: string;
  value?: string;
  defaultValue?: string;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  onValueChange?: (iso: string) => void;
  onBlur?: React.FocusEventHandler<HTMLButtonElement>;
  disabled?: boolean;
  min?: string | number;
  max?: string | number;
  placeholder?: string;
  className?: string;
  "aria-label"?: string;
  "aria-invalid"?: boolean;
};

function emitIsoChange(
  onChange: DatePickerProps["onChange"],
  name: string | undefined,
  iso: string,
) {
  onChange?.({
    target: { value: iso, name: name ?? "" },
    currentTarget: { value: iso, name: name ?? "" },
  } as React.ChangeEvent<HTMLInputElement>);
}

export const DatePicker = React.forwardRef<HTMLButtonElement, DatePickerProps>(
  function DatePicker(
    {
      id,
      name,
      value,
      defaultValue,
      onChange,
      onValueChange,
      onBlur,
      disabled,
      min,
      max,
      placeholder = "Pick a date",
      className,
      "aria-label": ariaLabel,
      "aria-invalid": ariaInvalid,
    },
    ref,
  ) {
    const [open, setOpen] = React.useState(false);
    const isControlled = value !== undefined;
    const [internalIso, setInternalIso] = React.useState(
      () => value ?? defaultValue ?? "",
    );

    React.useEffect(() => {
      if (isControlled) setInternalIso(value ?? "");
    }, [isControlled, value]);

    const isoValue = isControlled ? (value ?? "") : internalIso;
    const selectedDate = parseIsoDate(isoValue);
    const minDate = parseIsoDate(min == null ? undefined : String(min));
    const maxDate = parseIsoDate(max == null ? undefined : String(max));

    const disabledMatchers = React.useMemo(() => {
      const matchers: Matcher[] = [];
      if (minDate) matchers.push({ before: startOfDay(minDate) });
      if (maxDate) matchers.push({ after: startOfDay(maxDate) });
      return matchers.length ? matchers : undefined;
    }, [minDate, maxDate]);

    function handleSelect(date: Date | undefined) {
      const nextIso = date ? toIsoDate(date) : "";
      if (!isControlled) setInternalIso(nextIso);
      emitIsoChange(onChange, name, nextIso);
      onValueChange?.(nextIso);
      setOpen(false);
    }

    return (
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            ref={ref}
            type="button"
            id={id}
            name={name}
            disabled={disabled}
            aria-label={ariaLabel}
            aria-haspopup="dialog"
            aria-expanded={open}
            aria-invalid={ariaInvalid}
            onBlur={onBlur}
            className={cn(
              "flex h-10 w-full items-center rounded-lg border border-input bg-card px-3 text-left text-sm shadow-theme-xs transition-[color,background-color,border-color,box-shadow] duration-150 ease-theme",
              "hover:border-muted-foreground/40",
              "focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/20 focus-visible:outline-none",
              "disabled:cursor-not-allowed disabled:opacity-50",
              ariaInvalid && "border-destructive ring-destructive/20",
              selectedDate ? "text-foreground" : "text-muted-foreground",
              className,
            )}
          >
            <CalendarIcon
              className={cn(
                "mr-2 size-4 shrink-0",
                selectedDate ? "text-foreground" : "text-muted-foreground",
              )}
              aria-hidden
            />
            <span className="truncate">
              {selectedDate
                ? format(selectedDate, DISPLAY_FORMAT)
                : placeholder}
            </span>
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={handleSelect}
            disabled={disabledMatchers}
            fromDate={minDate}
            toDate={maxDate}
            autoFocus
          />
        </PopoverContent>
      </Popover>
    );
  },
);

export type DateRangePickerProps = {
  id?: string;
  from?: string;
  to?: string;
  onValueChange: (range: { from: string; to: string }) => void;
  disabled?: boolean;
  min?: string;
  max?: string;
  placeholder?: string;
  className?: string;
  "aria-label"?: string;
};

export function DateRangePicker({
  id,
  from,
  to,
  onValueChange,
  disabled,
  min,
  max,
  placeholder = "Pick a range",
  className,
  "aria-label": ariaLabel,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false);
  const isMobile = useIsMobile();
  const selectedFrom = parseIsoDate(from);
  const selectedTo = parseIsoDate(to);
  const minDate = parseIsoDate(min);
  const maxDate = parseIsoDate(max);
  const [draft, setDraft] = React.useState<DateRange | undefined>(() =>
    selectedFrom ? { from: selectedFrom, to: selectedTo } : undefined,
  );
  const [selectingEnd, setSelectingEnd] = React.useState(false);

  React.useEffect(() => {
    if (!open) {
      setDraft(
        selectedFrom ? { from: selectedFrom, to: selectedTo } : undefined,
      );
    }
  }, [open, from, to]);

  const disabledMatchers = React.useMemo(() => {
    const matchers: Matcher[] = [];
    if (minDate) matchers.push({ before: startOfDay(minDate) });
    if (maxDate) matchers.push({ after: startOfDay(maxDate) });
    return matchers.length ? matchers : undefined;
  }, [minDate, maxDate]);

  const displayValue = selectedFrom
    ? selectedTo
      ? `${format(selectedFrom, DISPLAY_FORMAT)} - ${format(selectedTo, DISPLAY_FORMAT)}`
      : format(selectedFrom, DISPLAY_FORMAT)
    : placeholder;

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (next) {
          setDraft(
            selectedFrom ? { from: selectedFrom, to: selectedTo } : undefined,
          );
          setSelectingEnd(false);
        }
      }}
    >
      <PopoverTrigger asChild>
        <button
          type="button"
          id={id}
          disabled={disabled}
          aria-label={ariaLabel}
          aria-haspopup="dialog"
          aria-expanded={open}
          className={cn(
            "flex h-10 w-full items-center rounded-lg border border-input bg-card px-3 text-left text-sm shadow-theme-xs transition-[color,background-color,border-color,box-shadow] duration-150 ease-theme",
            "hover:border-muted-foreground/40",
            "focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/20 focus-visible:outline-none",
            "disabled:cursor-not-allowed disabled:opacity-50",
            selectedFrom ? "text-foreground" : "text-muted-foreground",
            className,
          )}
        >
          <CalendarIcon
            className={cn(
              "mr-2 size-4 shrink-0",
              selectedFrom ? "text-foreground" : "text-muted-foreground",
            )}
            aria-hidden
          />
          <span className="truncate">{displayValue}</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="range"
          numberOfMonths={isMobile ? 1 : 2}
          selected={draft}
          // `onSelect` is what puts react-day-picker in controlled mode; without
          // it the calendar runs its own range algorithm and ignores `draft`.
          onSelect={(_range, day) => {
            if (!selectingEnd || !draft?.from) {
              setDraft({ from: day, to: undefined });
              setSelectingEnd(true);
              return;
            }

            const range =
              day < draft.from
                ? { from: day, to: draft.from }
                : { from: draft.from, to: day };
            setDraft(range);
            onValueChange({
              from: toIsoDate(range.from),
              to: toIsoDate(range.to),
            });
            setSelectingEnd(false);
            setOpen(false);
          }}
          disabled={disabledMatchers}
          fromDate={minDate}
          toDate={maxDate}
          defaultMonth={draft?.from ?? selectedFrom}
          autoFocus
        />
      </PopoverContent>
    </Popover>
  );
}
