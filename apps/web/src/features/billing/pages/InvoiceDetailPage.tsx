import { Link } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ChevronLeft, Landmark, Receipt } from "lucide-react";
import { api } from "@/lib/apiClient";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ActivityTrail } from "@/features/audit-log/components/ActivityTrail";
import { PaymentDialog } from "@/features/billing/components/PaymentDialog";
import { openReceiptPdf } from "@/features/billing/lib/receiptPdf";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Money } from "@/components/Money";
import { PaymentStatus } from "@/components/StatusIndicator";
import { Button } from "@/components/ui/button";
import { InvoiceDetailSkeleton } from "@/components/skeletons/PageSkeletons";

type Props = { patientId: string; invoiceId: string };

export function InvoiceDetailPage({ patientId, invoiceId }: Props) {
  const { data: invoice, refetch } = useQuery({
    queryKey: ["invoice", invoiceId],
    queryFn: () => api.getInvoice(invoiceId),
  });
  const [creditAmount, setCreditAmount] = useState("");
  const [creditReason, setCreditReason] = useState("");
  const credit = useMutation({
    mutationFn: () =>
      api.createCreditNote(invoiceId, {
        kind: "refund",
        amount: creditAmount,
        reason: creditReason.trim(),
      }),
    onSuccess: () => {
      setCreditAmount("");
      setCreditReason("");
      void refetch();
    },
  });
  const sendToFinancing = useMutation({
    mutationFn: () => api.sendInvoiceToFinancing(invoiceId),
    onSuccess: () => void refetch(),
  });

  if (!invoice) {
    return <InvoiceDetailSkeleton />;
  }

  return (
    <div className={pageContainerClass("narrow", "min-w-0")}>
      <Link
        to="/dashboard/patients/$patientId"
        params={{ patientId }}
        className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="size-4" />
        Patient
      </Link>

      <PageHeader
        title={invoice.invoice_number ?? "Draft"}
        actions={<PaymentStatus status={invoice.status} />}
      />

      <section>
        <ul className="mb-4 flex flex-col divide-y divide-border text-sm">
          {invoice.line_items.map((item) => (
            <li
              key={item.id}
              className="flex flex-wrap justify-between gap-2 py-2 first:pt-0"
            >
              <span className="min-w-0 break-words text-foreground">
                {item.description}
              </span>
              <Money
                amount={item.amount}
                className="shrink-0 text-muted-foreground"
              />
            </li>
          ))}
        </ul>

        <dl className="flex flex-col gap-1.5 border-t border-border pt-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Total</dt>
            <dd>
              <Money amount={invoice.total} />
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Paid</dt>
            <dd>
              <Money amount={invoice.amount_paid} />
            </dd>
          </div>
          <div className="flex justify-between font-medium">
            <dt className="text-foreground">Balance</dt>
            <dd>
              <Money amount={invoice.balance_due} />
            </dd>
          </div>
          {Number(invoice.amount_credited ?? 0) > 0 && (
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Credited</dt>
              <dd>
                <Money amount={invoice.amount_credited} />
              </dd>
            </div>
          )}
        </dl>
        {(invoice.credit_notes ?? []).length > 0 && (
          <ul className="mt-3 border-t border-border pt-3 text-sm">
            {invoice.credit_notes?.map((note) => (
              <li key={note.id} className="text-muted-foreground">
                {note.credit_number}: <Money amount={note.amount} /> (
                {note.kind})
              </li>
            ))}
          </ul>
        )}
      </section>

      {invoice.status !== "draft" &&
        invoice.status !== "void" &&
        Number(invoice.amount_paid) > 0 && (
          <section className="mt-6 flex flex-col gap-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="credit-amount">Credit</Label>
                <Input
                  id="credit-amount"
                  inputMode="decimal"
                  value={creditAmount}
                  onChange={(e) => setCreditAmount(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="credit-reason">Reason</Label>
                <Input
                  id="credit-reason"
                  value={creditReason}
                  onChange={(e) => setCreditReason(e.target.value)}
                />
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              className="w-fit"
              disabled={
                credit.isPending || !creditAmount || !creditReason.trim()
              }
              onClick={() => credit.mutate()}
            >
              Issue credit
            </Button>
          </section>
        )}

      {invoice.status !== "draft" && (
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <PaymentDialog
            invoiceId={invoiceId}
            balanceDue={invoice.balance_due}
            onPaid={() => void refetch()}
          />
          <Button
            variant="outline"
            onClick={() => void openReceiptPdf(invoiceId)}
          >
            <Receipt className="size-4" />
            Receipt
          </Button>
          {invoice.financing_available &&
            (invoice.financing_status ? (
              <p className="text-sm capitalize text-muted-foreground">
                Financing: {invoice.financing_status}
              </p>
            ) : (
              <Button
                variant="outline"
                disabled={sendToFinancing.isPending}
                onClick={() => sendToFinancing.mutate()}
              >
                <Landmark className="size-4" />
                Send to financing
              </Button>
            ))}
        </div>
      )}

      <div className="mt-4">
        <ActivityTrail targetType="invoice" targetId={invoiceId} />
      </div>
    </div>
  );
}
