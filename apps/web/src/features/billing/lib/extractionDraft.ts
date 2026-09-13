import type { InvoiceLineItemInput } from "@/lib/apiClient";

export type ExtractionField = {
  value: string | null;
  confidence: "high" | "low" | "missing";
};

export type BillingExtractionDraft = {
  attempt_id: string;
  fields: {
    amount: ExtractionField;
    date: ExtractionField;
    provider: ExtractionField;
    reference_number: ExtractionField;
  };
  source_preview_url?: string | null;
};

export function extractionToLineItem(
  draft: BillingExtractionDraft,
): InvoiceLineItemInput {
  const provider = draft.fields.provider.value?.trim();
  const ref = draft.fields.reference_number.value?.trim();
  const description =
    [provider, ref ? `Ref ${ref}` : null].filter(Boolean).join(" - ") ||
    "Receipt line";
  const amount = draft.fields.amount.value ?? "0";
  return {
    description,
    category: "other",
    quantity: "1",
    unit_price: amount,
  };
}

export function confidenceClass(
  confidence: ExtractionField["confidence"],
): string {
  if (confidence === "high")
    return "border-success-500/40 bg-success-50 dark:bg-success/10";
  if (confidence === "low")
    return "border-warning-500/40 bg-warning-50 dark:bg-warning/10";
  return "border-border bg-secondary/40";
}
