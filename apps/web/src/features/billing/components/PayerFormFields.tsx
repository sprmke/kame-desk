import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { api, type PayerType } from "@/lib/apiClient";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { Field } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
import { SearchInput } from "@/components/ui/search-input";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PatientFieldState } from "@/features/billing/hooks/usePatientField";

export const PAYER_TYPES: { value: PayerType; label: string }[] = [
  { value: "hmo", label: "HMO" },
  { value: "philhealth", label: "PhilHealth" },
  { value: "self_pay", label: "Self-pay" },
  { value: "other", label: "Other" },
];

export function PayerTypeSelect({
  id,
  value,
  onChange,
  allowEmpty,
}: {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  allowEmpty?: boolean;
}) {
  return (
    <Select
      value={allowEmpty ? value || "all" : value}
      onValueChange={(next) =>
        onChange(allowEmpty && next === "all" ? "" : next)
      }
    >
      <SelectTrigger id={id} className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {allowEmpty ? (
          <SelectItem value="all">All payer types</SelectItem>
        ) : null}
        {PAYER_TYPES.map((type) => (
          <SelectItem key={type.value} value={type.value}>
            {type.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/** Compact status control used as a row action inside payer workflow lists. */
export function RowStatusSelect({
  value,
  options,
  ariaLabel,
  onChange,
  disabled,
}: {
  value: string;
  options: readonly string[];
  ariaLabel: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger size="sm" className="w-[130px]" aria-label={ariaLabel}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option} value={option}>
            {option}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/**
 * Payer name input backed by the clinic's payer directory, so claim, eligibility,
 * and LOA forms all spell the same HMO the same way.
 */
export function PayerNameField({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const { data: payers } = useQuery({
    queryKey: ["payers"],
    queryFn: () => api.listPayers(),
  });
  const options = (payers ?? []).filter((payer) => payer.is_active);

  return (
    <Field>
      <FieldLabel htmlFor={id} label={label} required />
      <Input
        id={id}
        list={`${id}-options`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={FORM_PLACEHOLDERS.hmo}
        autoComplete="off"
      />
      <datalist id={`${id}-options`}>
        {options.map((payer) => (
          <option key={payer.id} value={payer.name} />
        ))}
      </datalist>
    </Field>
  );
}

export function PatientField({
  id,
  field,
}: {
  id: string;
  field: PatientFieldState;
}) {
  const enabled = !field.id && field.query.trim().length >= 2;
  const { data: matches } = useQuery({
    queryKey: ["patients", field.query],
    queryFn: () => api.listPatients({ q: field.query, page_size: 8 }),
    enabled,
  });

  if (field.id) {
    return (
      <Field>
        <FieldLabel htmlFor={id} label="Patient" required />
        <div
          id={id}
          className="flex min-h-11 items-center justify-between gap-2 rounded-md border border-border px-3 py-2 text-sm"
        >
          <span className="truncate font-medium text-foreground">
            {field.name}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Clear patient"
            onClick={field.reset}
          >
            <X className="size-4" />
          </Button>
        </div>
      </Field>
    );
  }

  return (
    <Field>
      <FieldLabel htmlFor={id} label="Patient" required />
      <SearchInput
        id={id}
        value={field.query}
        onChange={(e) => field.onQueryChange(e.target.value)}
        placeholder={FORM_PLACEHOLDERS.searchPatients}
        autoComplete="off"
      />
      {enabled && matches?.items.length ? (
        <ul className="max-h-48 overflow-y-auto rounded-md border border-border text-sm">
          {matches.items.map((patient) => (
            <li key={patient.id}>
              <button
                type="button"
                className="w-full cursor-pointer px-3 py-2 text-left hover:bg-muted"
                onClick={() => field.onSelect(patient.id, patient.full_name)}
              >
                {patient.full_name}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </Field>
  );
}
