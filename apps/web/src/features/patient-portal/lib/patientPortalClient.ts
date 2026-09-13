import { ApiError } from "@/lib/apiError";
import {
  clearPatientAuth,
  getPatientAccessToken,
  savePatientAuth,
} from "@/lib/patientPortalAuth";

import { API_BASE } from "@/lib/apiBase";

export type PatientPortalMe = {
  id: string;
  clinic_id: string;
  clinic_name: string;
  full_name: string;
  email: string | null;
  contact_number: string | null;
};

export type PatientPortalVisit = {
  id: string;
  scheduled_start: string;
  doctor_name: string;
  reason_for_visit: string | null;
  appointment_status: string;
  current_visit_status: string | null;
};

export type PatientPortalDiagnosis = {
  visit_date: string;
  doctor_name: string;
  diagnosis_primary: string | null;
  diagnosis_secondary: string[] | null;
  icd10_codes: string[] | null;
  follow_up_date: string | null;
};

export type PatientPortalVital = {
  recorded_at: string;
  height_cm: string | null;
  weight_kg: string | null;
  bmi: string | null;
  blood_pressure: string | null;
  temperature_c: string | null;
  heart_rate: number | null;
  respiratory_rate: number | null;
  spo2: number | null;
};

export type PatientPortalChartSummary = {
  diagnoses: PatientPortalDiagnosis[];
  vitals: PatientPortalVital[];
};

export type PatientPortalInvoice = {
  id: string;
  invoice_number: string | null;
  status: string;
  total: string;
  amount_paid: string;
  balance: string;
  issued_at: string | null;
};

export type PatientPortalInvoiceList = {
  items: PatientPortalInvoice[];
  total_balance: string;
};

export type PatientPortalDocument = {
  id: string;
  file_type: string;
  description: string | null;
  uploaded_at: string;
};

function redirectToPortalLogin() {
  clearPatientAuth();
  if (typeof window === "undefined") return;
  const match = window.location.pathname.match(/^\/patient-portal\/([^/]+)/);
  const loginPath = match
    ? `/patient-portal/${match[1]}/login`
    : "/patient-portal";
  if (window.location.pathname !== loginPath) {
    window.location.assign(loginPath);
  }
}

async function patientFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getPatientAccessToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/patient-portal/login/")) {
      redirectToPortalLogin();
    }
    const body = await res.json().catch(() => ({}));
    const message =
      typeof body.detail === "string" ? body.detail : "Request failed";
    throw new ApiError(message, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const patientPortalApi = {
  requestLogin: (clinicSlug: string, identifier: string) =>
    patientFetch<{ message: string }>("/patient-portal/login/request", {
      method: "POST",
      body: JSON.stringify({ clinic_slug: clinicSlug, identifier }),
    }),

  verifyLogin: async (token: string) => {
    const session = await patientFetch<{
      access_token: string;
      expires_in_minutes: number;
      patient_id: string;
      clinic_id: string;
    }>("/patient-portal/login/verify", {
      method: "POST",
      body: JSON.stringify({ token }),
    });
    savePatientAuth(
      session.access_token,
      session.patient_id,
      session.clinic_id,
    );
    return session;
  },

  getMe: () => patientFetch<PatientPortalMe>("/patient-portal/me"),

  getVisits: () => patientFetch<PatientPortalVisit[]>("/patient-portal/visits"),

  getChartSummary: () =>
    patientFetch<PatientPortalChartSummary>("/patient-portal/chart-summary"),

  getInvoices: () =>
    patientFetch<PatientPortalInvoiceList>("/patient-portal/invoices"),

  getDocuments: () =>
    patientFetch<PatientPortalDocument[]>("/patient-portal/documents"),

  getDocumentDownloadUrl: (fileId: string) =>
    patientFetch<{ download_url: string }>(
      `/patient-portal/documents/${fileId}/download`,
    ),
};
