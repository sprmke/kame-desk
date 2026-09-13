import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ResponsiveModal,
  ResponsiveModalContent,
  ResponsiveModalFooter,
  ResponsiveModalHeader,
  ResponsiveModalTitle,
  ResponsiveModalTrigger,
} from "@/components/ui/responsive-modal";

type Props = {
  invoiceId: string;
  balanceDue: string;
  onPaid: () => void;
};

const METHODS = ["cash", "gcash", "card", "bank_transfer"] as const;

export function PaymentDialog({ invoiceId, balanceDue, onPaid }: Props) {
  const [open, setOpen] = useState(false);
  const [method, setMethod] = useState<string>("cash");
  const [amount, setAmount] = useState(balanceDue);
  const [reference, setReference] = useState("");

  const pay = useMutation({
    mutationFn: () =>
      api.recordPayment(invoiceId, {
        method,
        amount,
        reference_number: reference || undefined,
      }),
    onSuccess: () => {
      setOpen(false);
      onPaid();
    },
  });

  return (
    <ResponsiveModal
      open={open}
      onOpenChange={(next) => {
        if (next) setAmount(balanceDue);
        setOpen(next);
      }}
    >
      <ResponsiveModalTrigger asChild>
        <Button variant="outline" disabled={Number(balanceDue) <= 0}>
          Pay
        </Button>
      </ResponsiveModalTrigger>
      <ResponsiveModalContent className="max-w-sm">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>Record payment</ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <form
          className="flex flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            pay.mutate();
          }}
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="method">Method</Label>
            <Select value={method} onValueChange={setMethod}>
              <SelectTrigger id="method" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {METHODS.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m.replace("_", " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="amount">Amount</Label>
            <Input
              id="amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reference">Reference</Label>
            <Input
              id="reference"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
            />
          </div>
          <ResponsiveModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={pay.isPending}>
              {pay.isPending ? "Recording…" : "Record"}
            </Button>
          </ResponsiveModalFooter>
        </form>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}
