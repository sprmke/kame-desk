import type { BirCompliance } from "@/lib/apiClient";
import { getAccessToken, getClinicId } from "@/lib/auth";

import { API_BASE } from "@/lib/apiBase";

export async function openReceiptPdf(invoiceId: string) {
  const token = getAccessToken();
  const clinicId = getClinicId();
  const res = await fetch(`${API_BASE}/invoices/${invoiceId}/receipt-pdf`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(clinicId ? { "X-Clinic-Id": clinicId } : {}),
    },
  });
  if (!res.ok) throw new Error("PDF failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
}

export async function openBirCompliancePreviewPdf(
  clinicId: string,
  data: BirCompliance,
) {
  const token = getAccessToken();
  const res = await fetch(
    `${API_BASE}/clinics/${clinicId}/bir-compliance/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        "X-Clinic-Id": clinicId,
      },
      body: JSON.stringify(data),
    },
  );
  if (!res.ok) throw new Error("PDF preview failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
}
