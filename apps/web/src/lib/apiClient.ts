import { API_BASE } from "@/lib/apiBase";
import {
  clearAuth,
  getAccessToken,
  getClinicId,
  getRefreshToken,
  saveAuth,
} from "@/lib/auth";
import { ApiError } from "@/lib/apiError";

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type AuthResponse = {
  user_id: string;
  email: string;
  full_name: string;
  clinic_id: string;
  clinic_name: string;
  role: string;
  tokens: TokenPair;
};

export type OnboardingStep = { key: string; label: string; complete: boolean };
export type OnboardingStatus = {
  steps: OnboardingStep[];
  all_complete: boolean;
  current_step: string | null;
};

export type Clinic = {
  id: string;
  name: string;
  address: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  license_info: string | null;
  accreditation_info: string | null;
  logo_url?: string | null;
  brand_color?: string | null;
  working_hours: Record<
    string,
    { open: string; close: string; closed: boolean }
  > | null;
  holiday_dates: string[] | null;
  default_appointment_duration_minutes: number;
  onboarding_completed_at: string | null;
  slug: string;
  public_booking_auto_confirm: boolean;
  ai_assistant_enabled?: boolean;
  assistant_disabled_tools?: string[];
  status?: string;
  plan_key?: string | null;
  organization_id?: string | null;
  reception_can_view_soap?: boolean;
  deletion_requested_at?: string | null;
  receipt_numbering?: {
    prefix: string;
    next_number: number;
    pad_width: number;
  } | null;
  bir_compliance?: BirCompliance | null;
  growth_settings?: GrowthSettings | null;
};

export type GrowthSettings = {
  google_review_link: string | null;
  review_requests_enabled: boolean;
  doh_accreditation_number: string | null;
  doh_accreditation_valid_until: string | null;
};

export type BirComplianceMode = "not_yet_accredited" | "ptu" | "cas";

export type BirCompliance = {
  tin: string | null;
  registered_name: string | null;
  registered_address: string | null;
  vat_registered: boolean;
  compliance_mode: BirComplianceMode;
  accreditation_number: string | null;
  accreditation_valid_until: string | null;
};

export type Membership = {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
};

export type SessionUser = {
  id: string;
  email: string;
  full_name: string;
  memberships: Array<{
    clinic_id: string;
    clinic_name: string;
    organization_id?: string | null;
    organization_name?: string | null;
    role: string;
    is_active: boolean;
  }>;
  organizations?: Array<{
    id: string;
    name: string;
    slug: string;
    status: string;
    is_owner: boolean;
  }>;
  email_verified_at?: string | null;
  is_platform_admin?: boolean;
  active_clinic?: {
    id: string;
    name: string;
    role: string;
  } | null;
  permissions?: string[];
};

export type DoctorProfile = {
  id: string;
  user_id: string;
  clinic_id: string;
  specialty: string | null;
  prc_license_number: string | null;
  signature_image_key: string | null;
  consultation_fee: string | null;
  follow_up_fee: string | null;
  full_name?: string | null;
};

export type Invitation = {
  id: string;
  email: string;
  role: string;
  accepted_at: string | null;
  revoked_at: string | null;
};

export type Patient = {
  id: string;
  clinic_id: string;
  patient_number: number;
  full_name: string;
  birthdate: string | null;
  sex: string | null;
  civil_status: string | null;
  occupation: string | null;
  contact_number: string | null;
  email: string | null;
  address: string | null;
  emergency_contact: Record<string, string> | null;
  insurance_info: Record<string, string> | null;
  is_archived: boolean;
  reminders_opted_out?: boolean;
};

export type PatientListResponse = {
  items: Patient[];
  total: number;
  page: number;
  page_size: number;
};

export type AllergyEntry = {
  substance: string;
  reaction?: string | null;
  severity?: "mild" | "moderate" | "severe" | null;
};

export type MedicalInfo = {
  allergies_reviewed: boolean;
  allergies: AllergyEntry[];
  medical_history: string | null;
  family_history: string | null;
  surgical_history: string | null;
  current_medications: Array<{ name: string; dose?: string | null }>;
  chronic_conditions: string[];
  vaccination_history: string[];
  clinical_notes: string | null;
};

export type Vitals = {
  id: string;
  patient_id: string;
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

export type PatientFile = {
  id: string;
  file_type: string;
  description: string | null;
  uploaded_at: string;
  download_url?: string | null;
};

export type Appointment = {
  id: string;
  clinic_id: string;
  patient_id: string;
  doctor_id: string;
  room_id: string | null;
  room_name?: string | null;
  service_fee_id?: string | null;
  booking_source?: string;
  scheduled_start: string;
  scheduled_end: string;
  reason_for_visit: string | null;
  notes: string | null;
  appointment_status: string;
  current_visit_status?: string | null;
  series_id?: string | null;
  series_occurrence_index?: number | null;
  patient_name?: string | null;
  doctor_name?: string | null;
  no_show_risk?: { level: string; score: number; reasons: string[] } | null;
};

export type WaitingRoomResponse = {
  items: WaitingRoomItem[];
  date: string;
};

export type WaitingRoomItem = {
  id: string;
  patient_id: string;
  patient_name?: string | null;
  doctor_id: string;
  doctor_name?: string | null;
  scheduled_start: string;
  scheduled_end: string;
  appointment_status: string;
  current_visit_status: string | null;
  reason_for_visit?: string | null;
};

export type AppointmentListResponse = {
  items: Appointment[];
  total: number;
  page?: number;
  page_size?: number;
};

export type SpecialtyTemplate = {
  template_key: string;
  name: string;
  schema_version: number;
  description?: string | null;
};

export type ToothCondition =
  | "sound"
  | "caries"
  | "filled"
  | "missing"
  | "crown"
  | "root_canal"
  | "extraction_planned"
  | "impacted"
  | "fractured";

export type ToothSurface =
  "mesial" | "distal" | "occlusal" | "buccal" | "lingual" | "incisal";

export type ToothEntryStatus = "existing" | "planned" | "completed";

export type ToothChartEntry = {
  id: string;
  clinic_id: string;
  patient_id: string;
  appointment_id: string | null;
  soap_note_id: string | null;
  tooth_number: number;
  surface: ToothSurface | null;
  condition: ToothCondition;
  status: ToothEntryStatus;
  procedure_code: string | null;
  invoice_line_item_id: string | null;
  noted_at: string;
  created_at: string;
};

export type SoapNote = {
  id: string;
  appointment_id: string;
  patient_id: string;
  doctor_id: string;
  clinic_id: string;
  version_number: number;
  subjective: string | null;
  objective: string | null;
  assessment: string | null;
  plan: string | null;
  diagnosis_primary: string | null;
  diagnosis_secondary: string[] | null;
  icd10_codes: string[] | null;
  follow_up_date: string | null;
  specialty_template_key: string | null;
  specialty_data: Record<string, unknown> | null;
  signed_at: string | null;
  signature_image_url: string | null;
  created_by_user_id: string;
  created_at: string;
  author_name?: string | null;
};

export type SoapNoteListResponse = {
  items: SoapNote[];
  latest_version: number | null;
};

export type ConsultationRecording = {
  id: string;
  appointment_id: string;
  clinic_id: string;
  duration_seconds: number | null;
  transcription_status: string;
  transcript_text: string | null;
  created_at: string;
};

export type RecordingUploadResponse = {
  recording: ConsultationRecording;
  upload_url: string;
  object_key: string;
};

export type ChartSearchResult = {
  soap_note_id: string;
  appointment_id: string;
  patient_id: string;
  patient_name: string;
  version_number: number;
  snippet: string;
  visit_date: string;
  score: number;
};

export type PrescriptionItemInput = {
  drug_name: string;
  generic_name?: string;
  dosage?: string;
  form?: string;
  frequency?: string;
  duration?: string;
  quantity?: string;
  special_instructions?: string;
};

export type ConflictFlag = {
  type: string;
  drug_name: string;
  message: string;
  related?: string | null;
};

export type BillingExtractionField = {
  value: string | null;
  confidence: string;
};

export type BillingExtractionResponse = {
  attempt_id: string;
  fields: {
    amount: BillingExtractionField;
    date: BillingExtractionField;
    provider: BillingExtractionField;
    reference_number: BillingExtractionField;
  };
  source_preview_url?: string | null;
};

export type Prescription = {
  id: string;
  patient_id: string;
  doctor_id: string;
  clinic_id: string;
  appointment_id: string | null;
  status: string;
  notes: string | null;
  issued_at: string | null;
  voided_at: string | null;
  void_reason: string | null;
  override_reason: string | null;
  conflict_flags: ConflictFlag[] | null;
  created_at: string;
  items: Array<PrescriptionItemInput & { id: string; sort_order: number }>;
  doctor_name?: string | null;
  pdf_download_url?: string | null;
};

export type ServiceFee = {
  id: string;
  clinic_id: string;
  name: string;
  amount: string;
  category: string | null;
  duration_minutes?: number | null;
};

export type ClinicRoom = {
  id: string;
  clinic_id: string;
  name: string;
  is_active: boolean;
};

export type WaitlistEntry = {
  id: string;
  clinic_id: string;
  patient_id: string;
  doctor_id: string | null;
  preferred_date: string | null;
  notes: string | null;
  status: string;
  booked_appointment_id: string | null;
  created_at: string;
  patient_name?: string | null;
  doctor_name?: string | null;
};

export type InvoiceLineItem = {
  id: string;
  description: string;
  category: string;
  quantity: string;
  unit_price: string;
  amount: string;
  hmo_covered_amount: string | null;
  hmo_claim_reference: string | null;
  sort_order: number;
};

export type InvoiceLineItemInput = {
  description: string;
  category: string;
  quantity: string;
  unit_price: string;
  hmo_covered_amount?: string | null;
  hmo_claim_reference?: string | null;
};

export type Invoice = {
  id: string;
  clinic_id: string;
  patient_id: string;
  appointment_id: string | null;
  invoice_number: string | null;
  status: string;
  subtotal: string;
  total: string;
  void_reason: string | null;
  issued_at: string | null;
  voided_at: string | null;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
  line_items: InvoiceLineItem[];
  amount_paid: string;
  balance_due: string;
  amount_credited?: string;
  credit_notes?: Array<{
    id: string;
    credit_number: string;
    kind: string;
    amount: string;
    reason: string;
    created_at: string;
  }>;
  patient_name?: string | null;
  financing_status?: string | null;
  financing_available?: boolean;
};

export type MembershipBillingInterval = "monthly" | "quarterly" | "annual";

export type MembershipIncludedService = {
  category: string;
  count_per_period: number;
};

export type MembershipPlan = {
  id: string;
  clinic_id: string;
  name: string;
  price: string;
  billing_interval: MembershipBillingInterval;
  included_services: MembershipIncludedService[];
  is_active: boolean;
};

export type PatientMembership = {
  id: string;
  clinic_id: string;
  patient_id: string;
  plan_id: string;
  plan_name?: string | null;
  status: string;
  started_at: string;
  current_period_end: string;
  usage_this_period: Record<string, number>;
  cancelled_at: string | null;
};

export type ChartShare = {
  share_url: string;
  expires_at: string;
};

export type PayerType = "hmo" | "philhealth" | "self_pay" | "other";

export type InsuranceClaim = {
  id: string;
  patient_id: string;
  invoice_id: string | null;
  provider: string;
  payer_type: PayerType;
  member_id: string | null;
  claim_reference: string | null;
  amount: string;
  status: string;
  notes: string | null;
  loa_request_id: string | null;
  created_at: string;
  patient_name?: string | null;
  invoice_number?: string | null;
};

export type Payer = {
  id: string;
  clinic_id: string;
  name: string;
  payer_type: PayerType;
  is_active: boolean;
};

export type EligibilityCheck = {
  id: string;
  patient_id: string;
  payer_name: string;
  payer_type: PayerType;
  member_id: string | null;
  status: "pending" | "verified" | "denied" | "expired";
  verified_amount: string | null;
  notes: string | null;
  checked_by_user_id: string;
  checked_at: string;
  patient_name?: string | null;
};

export type LoaRequest = {
  id: string;
  patient_id: string;
  claim_id: string | null;
  hmo_name: string;
  status: "requested" | "submitted" | "approved" | "denied";
  reference_number: string | null;
  document_object_key: string | null;
  requested_by_user_id: string;
  submitted_at: string | null;
  decided_at: string | null;
  decision_notes: string | null;
  created_at: string;
  patient_name?: string | null;
};

export type PatientBalance = {
  patient_id: string;
  outstanding_balance: string;
  invoice_count: number;
};

export type RevenueSummary = {
  today: string;
  week: string;
  month: string;
};

export type OutstandingBalanceEntry = {
  patient_id: string;
  patient_name: string;
  outstanding_balance: string;
  oldest_invoice_date: string | null;
};

export type DocumentTemplate = {
  id: string;
  clinic_id: string | null;
  template_key: string;
  name: string;
  template_type: string;
  body_template: string | null;
  is_active: boolean;
};

export type GeneratedDocument = {
  id: string;
  clinic_id: string;
  patient_id: string;
  appointment_id: string | null;
  template_id: string;
  document_type: string;
  status: string;
  preview_content: string;
  final_content_snapshot: string | null;
  patient_file_id: string | null;
  issued_at: string | null;
  created_at: string;
  template_name?: string | null;
  referral_recipient?: string | null;
  referral_status?: string | null;
  referral_outcome?: string | null;
  chart_share_expires_at?: string | null;
};

export type NotificationPreferencesResponse = {
  preferences: Record<string, unknown>;
  sms_configured: boolean;
  whatsapp_configured: boolean;
};

export type PatientRecall = {
  id: string;
  patient_id: string;
  source: string;
  due_date: string;
  status: string;
  source_soap_note_id: string | null;
  created_at: string;
  patient_name?: string | null;
};

export type ReportResponse = {
  series: Array<Record<string, string | number | null>>;
  from_date: string;
  to_date: string;
  totals?: RevenueSummary;
};

export type NpsReportRow = {
  period: string;
  sent: number;
  responded: number;
  promoters: number;
  passives: number;
  detractors: number;
  nps_score: number | null;
};

export type NpsReportResponse = {
  series: NpsReportRow[];
  from_date: string;
  to_date: string;
};

export type PatientSurveyResponse = {
  id: string;
  patient_id: string;
  visit_id: string;
  score: number | null;
  comment: string | null;
  sent_at: string;
  responded_at: string | null;
};

export type ActivityLogEntry = {
  id: string;
  clinic_id: string | null;
  actor_user_id: string | null;
  actor_name: string | null;
  actor_type: string;
  action: string;
  target_type: string | null;
  target_id: string | null;
  summary: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

export type ActivityLogListResponse = {
  items: ActivityLogEntry[];
  total: number;
  page: number;
  page_size: number;
};

let refreshInFlight: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  const clinicId = getClinicId();
  if (!refreshToken || !clinicId) return false;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) return false;
        const tokens = (await res.json()) as TokenPair;
        saveAuth(tokens, clinicId);
        return true;
      } catch {
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }

  return refreshInFlight;
}

function redirectToLogin() {
  clearAuth();
  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

async function apiFetch<T>(
  path: string,
  init?: RequestInit,
  retried = false,
): Promise<T> {
  const token = getAccessToken();
  const clinicId = getClinicId();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(clinicId ? { "X-Clinic-Id": clinicId } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (res.status === 401 && !retried && !path.startsWith("/auth/")) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return apiFetch<T>(path, init, true);
    redirectToLogin();
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    let message = "Request failed";
    let code: string | undefined;
    if (typeof detail === "string") {
      message = detail;
    } else if (typeof detail === "object" && detail !== null) {
      if ("message" in detail && typeof detail.message === "string") {
        message = detail.message;
      } else if ("detail" in detail) {
        message = String(detail.detail);
      }
      if ("code" in detail && typeof detail.code === "string") {
        code = detail.code;
      }
    }
    const err = new ApiError(message, res.status, code);
    if (
      code === "NO_ACTIVE_MEMBERSHIP" &&
      typeof window !== "undefined" &&
      !path.startsWith("/auth/me")
    ) {
      window.dispatchEvent(new CustomEvent("doctordesk:membership-lost"));
    }
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function apiDownload(path: string, filename: string): Promise<void> {
  const token = getAccessToken();
  const clinicId = getClinicId();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(clinicId ? { "X-Clinic-Id": clinicId } : {}),
    },
  });
  if (res.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return apiDownload(path, filename);
    redirectToLogin();
    return;
  }
  if (!res.ok) {
    throw new ApiError("Download failed", res.status);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

async function apiUpload<T>(path: string, file: File): Promise<T> {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  const content_base64 = btoa(binary);
  return apiFetch<T>(path, {
    method: "POST",
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type || "application/octet-stream",
      content_base64,
    }),
  });
}

export const api = {
  register: (body: {
    email: string;
    password: string;
    full_name: string;
    clinic_name: string;
    plan_key?: string;
  }) =>
    apiFetch<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  login: (body: { email: string; password: string }) =>
    apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  forgotPassword: (email: string) =>
    apiFetch<void>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  resetPassword: (token: string, password: string) =>
    apiFetch<void>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, password }),
    }),
  verifyEmail: (token: string) =>
    apiFetch<void>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),
  listSessions: () =>
    apiFetch<
      Array<{
        id: string;
        created_at: string;
        expires_at: string;
        is_current: boolean;
      }>
    >("/auth/sessions"),
  logoutEverywhere: () =>
    apiFetch<void>("/auth/logout-everywhere", { method: "POST" }),
  logout: (refresh_token: string) =>
    apiFetch<void>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),
  me: () => apiFetch<SessionUser>("/auth/me"),
  listPublicPlans: () =>
    apiFetch<
      Array<{
        key: string;
        name: string;
        monthly_php: number;
        trial_days: number;
        included: string;
      }>
    >("/plans"),
  getAssistantUsage: () =>
    apiFetch<{
      days: Array<{ date: string; requests: number; tokens: number }>;
      request_total: number;
      daily_cap: number;
    }>("/assistant/usage"),
  listPlatformTenants: (q?: string) =>
    apiFetch<
      Array<{
        id: string;
        name: string;
        status: string;
        plan_key: string;
        slug: string;
        clinic_count?: number;
        tenant_type?: string;
      }>
    >(`/platform/tenants${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  getPlatformTenant: (orgId: string) =>
    apiFetch<{
      id: string;
      name: string;
      slug: string;
      status: string;
      plan_key: string;
      subscription_status: string;
      enrollments: Array<{
        id: string;
        clinic_id: string;
        clinic_name: string;
        clinic_slug: string;
        status: string;
        enrolled_at: string | null;
      }>;
    }>(`/platform/tenants/${orgId}`),
  patchPlatformTenant: (
    orgId: string,
    body: { status?: string; plan_key?: string },
  ) =>
    apiFetch<{
      id: string;
      name: string;
      status: string;
      plan_key: string;
    }>(`/platform/tenants/${orgId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  patchPlatformEnrollment: (
    orgId: string,
    clinicId: string,
    body: { status: string },
  ) =>
    apiFetch<{
      id: string;
      clinic_id: string;
      status: string;
      enrolled_at: string | null;
    }>(`/platform/tenants/${orgId}/enrollments/${clinicId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  impersonateTenant: (orgId: string) =>
    apiFetch<{
      organization_id?: string;
      clinic_id: string;
      access_token: string;
      impersonated_user_id: string;
      expires_minutes: number;
    }>(`/platform/tenants/${orgId}/impersonate`, { method: "POST" }),
  listOrganizations: () =>
    apiFetch<
      Array<{
        id: string;
        name: string;
        slug: string;
        status: string;
        is_owner: boolean;
      }>
    >("/organizations"),
  getOrganization: (orgId: string) =>
    apiFetch<{
      id: string;
      name: string;
      slug: string;
      status: string;
      is_owner: boolean;
      subscription: {
        plan_key: string;
        status: string;
        trial_ends_at: string | null;
      } | null;
      enrolled_clinics: Array<{
        id: string;
        clinic_id: string;
        clinic_name: string;
        clinic_slug: string;
        status: string;
        enrolled_at: string | null;
      }>;
    }>(`/organizations/${orgId}`),
  createClinicUnderOrg: (
    orgId: string,
    body: { name: string; slug?: string },
  ) =>
    apiFetch<{
      clinic_id: string;
      clinic_name: string;
      clinic_slug: string;
      enrollment_status: string;
      organization_id: string;
    }>(`/organizations/${orgId}/clinics`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getPlatformFlag: (key: string) =>
    apiFetch<{ key: string; enabled: boolean }>(`/platform/flags/${key}`),
  patchPlatformFlag: (key: string, enabled: boolean) =>
    apiFetch<{ key: string; enabled: boolean }>(`/platform/flags/${key}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    }),
  getPlatformMetrics: () =>
    apiFetch<{
      clinics_by_status: Record<string, number>;
      appointments_total: number;
      ai_requests: number;
      ai_tokens: number;
      sms_sent: number;
      sms_failed: number;
      files_total: number;
      clinics_by_ai_requests: {
        clinic_id: string;
        name: string;
        ai_requests: number;
      }[];
    }>("/platform/metrics"),

  getClinic: (clinicId: string) => apiFetch<Clinic>(`/clinics/${clinicId}`),
  patchClinic: (clinicId: string, body: Partial<Clinic>) =>
    apiFetch<Clinic>(`/clinics/${clinicId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  getGrowthSettings: (clinicId: string) =>
    apiFetch<GrowthSettings>(`/clinics/${clinicId}/growth-settings`),
  putGrowthSettings: (clinicId: string, body: GrowthSettings) =>
    apiFetch<GrowthSettings>(`/clinics/${clinicId}/growth-settings`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  clinicLogoUpload: (
    clinicId: string,
    body: { content_type: string; file_size_bytes: number },
  ) =>
    apiFetch<{ upload_url: string; object_key: string }>(
      `/clinics/${clinicId}/logo-upload`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  putWorkingHours: (
    clinicId: string,
    body: {
      working_hours: Record<
        string,
        { open: string; close: string; closed: boolean }
      >;
      holiday_dates: string[];
    },
  ) =>
    apiFetch<Clinic>(`/clinics/${clinicId}/working-hours`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  getReceiptNumbering: (clinicId: string) =>
    apiFetch<{ prefix: string; next_number: number; pad_width: number }>(
      `/clinics/${clinicId}/receipt-numbering`,
    ),
  putReceiptNumbering: (
    clinicId: string,
    body: { prefix: string; next_number: number; pad_width: number },
  ) =>
    apiFetch<{ prefix: string; next_number: number; pad_width: number }>(
      `/clinics/${clinicId}/receipt-numbering`,
      { method: "PUT", body: JSON.stringify(body) },
    ),
  getBirCompliance: (clinicId: string) =>
    apiFetch<BirCompliance>(`/clinics/${clinicId}/bir-compliance`),
  putBirCompliance: (clinicId: string, body: BirCompliance) =>
    apiFetch<BirCompliance>(`/clinics/${clinicId}/bir-compliance`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  getOnboardingStatus: (clinicId: string) =>
    apiFetch<OnboardingStatus>(`/clinics/${clinicId}/onboarding-status`),
  skipInvite: (clinicId: string) =>
    apiFetch<Clinic>(`/clinics/${clinicId}/onboarding/skip-invite`, {
      method: "POST",
    }),
  createDoctor: (clinicId: string, body: Record<string, unknown>) =>
    apiFetch<DoctorProfile>(`/clinics/${clinicId}/doctors`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  listDoctors: (clinicId: string) =>
    apiFetch<DoctorProfile[]>(`/clinics/${clinicId}/doctors`),
  patchDoctor: (doctorId: string, body: Record<string, unknown>) =>
    apiFetch<DoctorProfile>(`/doctors/${doctorId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  signatureUpload: (
    doctorId: string,
    body: { content_type: string; file_size_bytes: number },
  ) =>
    apiFetch<{ upload_url: string; object_key: string }>(
      `/doctors/${doctorId}/signature-upload`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  createServiceFee: (
    clinicId: string,
    body: {
      name: string;
      amount: number;
      category?: string;
      duration_minutes?: number;
    },
  ) =>
    apiFetch(`/clinics/${clinicId}/service-fees`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  listServiceFees: (clinicId: string) =>
    apiFetch<ServiceFee[]>(`/clinics/${clinicId}/service-fees`),
  listRooms: (clinicId: string) =>
    apiFetch<ClinicRoom[]>(`/clinics/${clinicId}/rooms`),
  createRoom: (clinicId: string, body: { name: string }) =>
    apiFetch<ClinicRoom>(`/clinics/${clinicId}/rooms`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchRoom: (
    clinicId: string,
    roomId: string,
    body: { name?: string; is_active?: boolean },
  ) =>
    apiFetch<ClinicRoom>(`/clinics/${clinicId}/rooms/${roomId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  listWaitlist: (params?: {
    status?: string;
    doctor_id?: string;
    preferred_date?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.status) search.set("status", params.status);
    if (params?.doctor_id) search.set("doctor_id", params.doctor_id);
    if (params?.preferred_date)
      search.set("preferred_date", params.preferred_date);
    const qs = search.toString();
    return apiFetch<WaitlistEntry[]>(
      `/appointments/waitlist${qs ? `?${qs}` : ""}`,
    );
  },
  createWaitlist: (body: {
    patient_id: string;
    doctor_id?: string;
    preferred_date?: string;
    notes?: string;
  }) =>
    apiFetch<WaitlistEntry>("/appointments/waitlist", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchWaitlist: (
    entryId: string,
    body: { status?: string; notes?: string; preferred_date?: string | null },
  ) =>
    apiFetch<WaitlistEntry>(`/appointments/waitlist/${entryId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  patchServiceFee: (
    clinicId: string,
    feeId: string,
    body: {
      name?: string;
      amount?: number;
      category?: string;
      duration_minutes?: number;
    },
  ) =>
    apiFetch<ServiceFee>(`/clinics/${clinicId}/service-fees/${feeId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteServiceFee: (clinicId: string, feeId: string) =>
    apiFetch<void>(`/clinics/${clinicId}/service-fees/${feeId}`, {
      method: "DELETE",
    }),
  createInvitation: (
    clinicId: string,
    body: { email: string; role: string; full_name?: string },
  ) =>
    apiFetch(`/clinics/${clinicId}/invitations`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getSeatSummary: (clinicId: string) =>
    apiFetch<{ limit: number | null; used: number; remaining: number | null }>(
      `/clinics/${clinicId}/seat-summary`,
    ),
  listMembers: (clinicId: string) =>
    apiFetch<Membership[]>(`/clinics/${clinicId}/members`),
  patchMember: (
    clinicId: string,
    membershipId: string,
    body: { role?: string; is_active?: boolean },
  ) =>
    apiFetch<Membership>(`/clinics/${clinicId}/members/${membershipId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  listInvitations: (clinicId: string) =>
    apiFetch<Invitation[]>(`/clinics/${clinicId}/invitations`),
  revokeInvitation: (clinicId: string, invitationId: string) =>
    apiFetch<void>(`/clinics/${clinicId}/invitations/${invitationId}`, {
      method: "DELETE",
    }),
  resendInvitation: (clinicId: string, invitationId: string) =>
    apiFetch<Invitation>(
      `/clinics/${clinicId}/invitations/${invitationId}/resend`,
      { method: "POST" },
    ),
  downloadPatientsCsv: (clinicId: string) =>
    apiDownload(`/clinics/${clinicId}/export/patients`, "patients.csv"),
  downloadAppointmentsCsv: (clinicId: string) =>
    apiDownload(`/clinics/${clinicId}/export/appointments`, "appointments.csv"),
  requestClinicDeletion: (clinicId: string) =>
    apiFetch<Clinic>(`/clinics/${clinicId}/deletion-request`, {
      method: "POST",
    }),
  acceptInvitation: (
    token: string,
    body: { full_name?: string; password?: string },
  ) =>
    apiFetch<void>(`/invitations/${token}/accept`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listPatients: (params?: {
    q?: string;
    page?: number;
    page_size?: number;
    sort?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.q) search.set("q", params.q);
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.sort) search.set("sort", params.sort);
    const qs = search.toString();
    return apiFetch<PatientListResponse>(`/patients${qs ? `?${qs}` : ""}`);
  },
  createPatient: (body: Record<string, unknown>) =>
    apiFetch<Patient>("/patients", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getPatient: (patientId: string) =>
    apiFetch<Patient>(`/patients/${patientId}`),
  findPatientMatches: (params: {
    full_name?: string;
    contact_number?: string;
  }) => {
    const search = new URLSearchParams();
    if (params.full_name) search.set("full_name", params.full_name);
    if (params.contact_number)
      search.set("contact_number", params.contact_number);
    const qs = search.toString();
    return apiFetch<Patient[]>(`/patients/matches${qs ? `?${qs}` : ""}`);
  },
  importPatients: (body: { csv: string; commit: boolean }) =>
    apiFetch<{
      items: Array<{
        full_name: string;
        birthdate: string | null;
        contact_number: string | null;
        email: string | null;
        match_count: number;
      }>;
      errors: string[];
      created: number;
      committed: boolean;
    }>("/patients/import", { method: "POST", body: JSON.stringify(body) }),
  mergePatients: (targetId: string, source_patient_id: string) =>
    apiFetch<Patient>(`/patients/${targetId}/merge`, {
      method: "POST",
      body: JSON.stringify({ source_patient_id }),
    }),
  patchPatient: (patientId: string, body: Record<string, unknown>) =>
    apiFetch<Patient>(`/patients/${patientId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  getMedicalInfo: (patientId: string) =>
    apiFetch<MedicalInfo>(`/patients/${patientId}/medical-info`),
  putMedicalInfo: (patientId: string, body: MedicalInfo) =>
    apiFetch<MedicalInfo>(`/patients/${patientId}/medical-info`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  listVitals: (patientId: string) =>
    apiFetch<Vitals[]>(`/patients/${patientId}/vitals`),
  recordVitals: (patientId: string, body: Record<string, unknown>) =>
    apiFetch<Vitals>(`/patients/${patientId}/vitals`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  listPatientFiles: (patientId: string) =>
    apiFetch<PatientFile[]>(`/patients/${patientId}/files`),

  listAppointments: (params?: {
    doctor_id?: string;
    patient_id?: string;
    status?: string;
    start_from?: string;
    start_to?: string;
    booking_source?: string;
    room_id?: string;
    q?: string;
    page?: number;
    page_size?: number;
    sort?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.doctor_id) search.set("doctor_id", params.doctor_id);
    if (params?.patient_id) search.set("patient_id", params.patient_id);
    if (params?.status) search.set("status", params.status);
    if (params?.start_from) search.set("start_from", params.start_from);
    if (params?.start_to) search.set("start_to", params.start_to);
    if (params?.booking_source)
      search.set("booking_source", params.booking_source);
    if (params?.room_id) search.set("room_id", params.room_id);
    if (params?.q) search.set("q", params.q);
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.sort) search.set("sort", params.sort);
    const qs = search.toString();
    return apiFetch<AppointmentListResponse>(
      `/appointments${qs ? `?${qs}` : ""}`,
    );
  },
  createAppointment: (body: Record<string, unknown>) =>
    apiFetch<Appointment>("/appointments", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchAppointment: (appointmentId: string, body: Record<string, unknown>) =>
    apiFetch<Appointment>(`/appointments/${appointmentId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  rescheduleAppointment: (
    appointmentId: string,
    body: { scheduled_start: string; scheduled_end: string },
  ) =>
    apiFetch<Appointment>(`/appointments/${appointmentId}/reschedule`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  getAvailableSlots: (params: {
    doctor_id: string;
    date: string;
    duration_minutes?: number;
  }) => {
    const search = new URLSearchParams({
      doctor_id: params.doctor_id,
      date: params.date,
    });
    if (params.duration_minutes) {
      search.set("duration_minutes", String(params.duration_minutes));
    }
    return apiFetch<{
      slots: Array<{ scheduled_start: string; scheduled_end: string }>;
    }>(`/appointments/available-slots?${search}`);
  },
  getWaitingRoom: () =>
    apiFetch<WaitingRoomResponse>("/appointments/waiting-room"),
  updateVisitStatus: (
    appointmentId: string,
    visit_status: "Arrived" | "In Consultation" | "Completed",
  ) =>
    apiFetch<Appointment>(`/appointments/${appointmentId}/visit-status`, {
      method: "POST",
      body: JSON.stringify({ visit_status }),
    }),
  createWalkIn: (body: {
    doctor_id: string;
    patient_id?: string;
    new_patient?: { full_name: string };
    reason_for_visit?: string;
  }) =>
    apiFetch<Appointment>("/appointments/walk-in", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  markNoShow: (appointmentId: string) =>
    apiFetch<Appointment>(`/appointments/${appointmentId}/mark-no-show`, {
      method: "POST",
    }),
  createAppointmentSeries: (body: Record<string, unknown>) =>
    apiFetch<{
      series: { id: string };
      expansion: { created: number; conflicts: unknown[] };
    }>("/appointment-series", { method: "POST", body: JSON.stringify(body) }),
  cancelAppointment: (
    appointmentId: string,
    scope: "this" | "following" | "all" = "this",
  ) =>
    apiFetch<Appointment>(`/appointments/${appointmentId}?scope=${scope}`, {
      method: "DELETE",
    }),

  listSpecialtyTemplates: () =>
    apiFetch<SpecialtyTemplate[]>(`/specialty-templates`),
  listToothChart: (patientId: string) =>
    apiFetch<ToothChartEntry[]>(`/patients/${patientId}/tooth-chart`),
  createToothChartEntry: (
    patientId: string,
    body: {
      appointment_id?: string;
      soap_note_id?: string;
      tooth_number: number;
      surface?: ToothSurface;
      condition: ToothCondition;
      status?: ToothEntryStatus;
      procedure_code?: string;
    },
  ) =>
    apiFetch<ToothChartEntry>(`/patients/${patientId}/tooth-chart`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  addToothChartEntryToInvoice: (
    patientId: string,
    entryId: string,
    body: { description: string; amount: string; appointment_id?: string },
  ) =>
    apiFetch<{ entry: ToothChartEntry; invoice_id: string }>(
      `/patients/${patientId}/tooth-chart/${entryId}/add-to-invoice`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  listSoapNotes: (appointmentId: string, version?: number) => {
    const qs = version ? `?version=${version}` : "";
    return apiFetch<SoapNoteListResponse>(
      `/appointments/${appointmentId}/soap-notes${qs}`,
    );
  },
  createSoapNote: (appointmentId: string, body: Record<string, unknown>) =>
    apiFetch<SoapNote>(`/appointments/${appointmentId}/soap-notes`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  signSoapNote: (appointmentId: string, version: number) =>
    apiFetch<SoapNote>(
      `/appointments/${appointmentId}/soap-notes/${version}/sign`,
      { method: "POST" },
    ),

  listPrescriptions: (patientId: string) =>
    apiFetch<{ items: Prescription[]; total: number }>(
      `/patients/${patientId}/prescriptions`,
    ),
  createPrescription: (
    patientId: string,
    body: {
      appointment_id?: string;
      notes?: string;
      items: PrescriptionItemInput[];
    },
  ) =>
    apiFetch<Prescription>(`/patients/${patientId}/prescriptions`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  checkPrescriptionConflicts: (patientId: string, drug_names: string[]) =>
    apiFetch<{ flags: ConflictFlag[] }>(
      `/patients/${patientId}/prescription-conflicts`,
      { method: "POST", body: JSON.stringify({ drug_names }) },
    ),
  explainPrescriptionFlag: (patientId: string, flag: ConflictFlag) =>
    apiFetch<{ explanation: string; flag: ConflictFlag }>(
      `/patients/${patientId}/prescription-flag/explain`,
      { method: "POST", body: JSON.stringify({ flag }) },
    ),
  extractBillingDocument: (patientId: string, file: File) =>
    apiUpload<BillingExtractionResponse>(
      `/patients/${patientId}/billing-assist/extract`,
      file,
    ),
  confirmBillingExtraction: (patientId: string, attemptId: string) =>
    apiFetch<{ status: string }>(
      `/patients/${patientId}/billing-assist/confirm-attempt`,
      { method: "POST", body: JSON.stringify({ attempt_id: attemptId }) },
    ),
  issuePrescription: (
    prescriptionId: string,
    body: { override_reason?: string },
  ) =>
    apiFetch<Prescription>(`/prescriptions/${prescriptionId}/issue`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  voidPrescription: (prescriptionId: string, reason: string) =>
    apiFetch<Prescription>(`/prescriptions/${prescriptionId}/void`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),

  listInvoices: (patientId: string) =>
    apiFetch<{ items: Invoice[]; total: number }>(
      `/patients/${patientId}/invoices`,
    ),
  createInvoice: (
    patientId: string,
    body: { appointment_id?: string; line_items?: InvoiceLineItemInput[] },
  ) =>
    apiFetch<Invoice>(`/patients/${patientId}/invoices`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getInvoice: (invoiceId: string) =>
    apiFetch<Invoice>(`/invoices/${invoiceId}`),
  addInvoiceLineItem: (invoiceId: string, body: InvoiceLineItemInput) =>
    apiFetch<Invoice>(`/invoices/${invoiceId}/line-items`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  issueInvoice: (invoiceId: string) =>
    apiFetch<Invoice>(`/invoices/${invoiceId}/issue`, { method: "POST" }),
  recordPayment: (
    invoiceId: string,
    body: { method: string; amount: string; reference_number?: string },
  ) =>
    apiFetch<Invoice>(`/invoices/${invoiceId}/payments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  voidInvoice: (invoiceId: string, reason: string) =>
    apiFetch<Invoice>(`/invoices/${invoiceId}/void`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  listClinicInvoices: (params?: {
    q?: string;
    status?: string;
    start_from?: string;
    start_to?: string;
    page?: number;
    page_size?: number;
    sort?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.q) search.set("q", params.q);
    if (params?.status) search.set("status", params.status);
    if (params?.start_from) search.set("start_from", params.start_from);
    if (params?.start_to) search.set("start_to", params.start_to);
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.sort) search.set("sort", params.sort);
    const qs = search.toString();
    return apiFetch<{
      items: Invoice[];
      total: number;
      page?: number;
      page_size?: number;
    }>(`/invoices${qs ? `?${qs}` : ""}`);
  },
  exportClinicInvoicesCsv: async (params?: { q?: string; status?: string }) => {
    const search = new URLSearchParams();
    if (params?.q) search.set("q", params.q);
    if (params?.status) search.set("status", params.status);
    const token = getAccessToken();
    const clinicId = getClinicId();
    const qs = search.toString();
    const res = await fetch(
      `${API_BASE}/invoices/export${qs ? `?${qs}` : ""}`,
      {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(clinicId ? { "X-Clinic-Id": clinicId } : {}),
        },
      },
    );
    if (!res.ok) throw new Error("Export failed");
    return res.text();
  },
  createCreditNote: (
    invoiceId: string,
    body: { kind: "refund" | "adjustment"; amount: string; reason: string },
  ) =>
    apiFetch<Invoice>(`/invoices/${invoiceId}/credit-notes`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  sendInvoiceToFinancing: (invoiceId: string) =>
    apiFetch<Invoice>(`/invoices/${invoiceId}/send-to-financing`, {
      method: "POST",
    }),
  listClaims: (params?: {
    status?: string;
    patient_id?: string;
    payer_type?: string;
    q?: string;
    page?: number;
    page_size?: number;
    sort?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.status) search.set("status", params.status);
    if (params?.patient_id) search.set("patient_id", params.patient_id);
    if (params?.payer_type) search.set("payer_type", params.payer_type);
    if (params?.q) search.set("q", params.q);
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.sort) search.set("sort", params.sort);
    const qs = search.toString();
    return apiFetch<{
      items: InsuranceClaim[];
      total: number;
      page?: number;
      page_size?: number;
    }>(`/claims${qs ? `?${qs}` : ""}`);
  },
  createClaim: (body: {
    patient_id: string;
    invoice_id?: string;
    provider: string;
    payer_type?: PayerType;
    member_id?: string;
    claim_reference?: string;
    amount: string;
    notes?: string;
    loa_request_id?: string;
  }) =>
    apiFetch<InsuranceClaim>("/claims", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchClaim: (
    claimId: string,
    body: {
      status?: string;
      payer_type?: PayerType;
      claim_reference?: string;
      notes?: string;
      loa_request_id?: string;
    },
  ) =>
    apiFetch<InsuranceClaim>(`/claims/${claimId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  listPayers: () => apiFetch<Payer[]>("/payers"),
  createPayer: (body: { name: string; payer_type?: PayerType }) =>
    apiFetch<Payer>("/payers", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updatePayer: (
    payerId: string,
    body: { name?: string; payer_type?: PayerType; is_active?: boolean },
  ) =>
    apiFetch<Payer>(`/payers/${payerId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  listEligibilityChecks: (params?: {
    patient_id?: string;
    status?: string;
    payer_type?: string;
    q?: string;
    page?: number;
    page_size?: number;
    sort?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.patient_id) search.set("patient_id", params.patient_id);
    if (params?.status) search.set("status", params.status);
    if (params?.payer_type) search.set("payer_type", params.payer_type);
    if (params?.q) search.set("q", params.q);
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.sort) search.set("sort", params.sort);
    const qs = search.toString();
    return apiFetch<{ items: EligibilityCheck[]; total: number }>(
      `/eligibility-checks${qs ? `?${qs}` : ""}`,
    );
  },
  createEligibilityCheck: (body: {
    patient_id: string;
    payer_name: string;
    payer_type?: PayerType;
    member_id?: string;
    notes?: string;
  }) =>
    apiFetch<EligibilityCheck>("/eligibility-checks", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchEligibilityCheck: (
    checkId: string,
    body: {
      status?: EligibilityCheck["status"];
      verified_amount?: string;
      notes?: string;
    },
  ) =>
    apiFetch<EligibilityCheck>(`/eligibility-checks/${checkId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  listLoaRequests: (params?: {
    patient_id?: string;
    status?: string;
    q?: string;
    page?: number;
    page_size?: number;
    sort?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.patient_id) search.set("patient_id", params.patient_id);
    if (params?.status) search.set("status", params.status);
    if (params?.q) search.set("q", params.q);
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.sort) search.set("sort", params.sort);
    const qs = search.toString();
    return apiFetch<{ items: LoaRequest[]; total: number }>(
      `/loa-requests${qs ? `?${qs}` : ""}`,
    );
  },
  createLoaRequest: (body: {
    patient_id: string;
    claim_id?: string;
    hmo_name: string;
  }) =>
    apiFetch<LoaRequest>("/loa-requests", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchLoaRequest: (
    loaId: string,
    body: {
      status?: LoaRequest["status"];
      claim_id?: string;
      reference_number?: string;
      document_object_key?: string;
      decision_notes?: string;
    },
  ) =>
    apiFetch<LoaRequest>(`/loa-requests/${loaId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  getPatientBalance: (patientId: string) =>
    apiFetch<PatientBalance>(`/patients/${patientId}/balance`),
  listMembershipPlans: (clinicId: string) =>
    apiFetch<MembershipPlan[]>(`/clinics/${clinicId}/membership-plans`),
  createMembershipPlan: (
    clinicId: string,
    body: {
      name: string;
      price: string;
      billing_interval: MembershipBillingInterval;
      included_services: MembershipIncludedService[];
    },
  ) =>
    apiFetch<MembershipPlan>(`/clinics/${clinicId}/membership-plans`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateMembershipPlan: (
    clinicId: string,
    planId: string,
    body: Partial<{
      name: string;
      price: string;
      billing_interval: MembershipBillingInterval;
      included_services: MembershipIncludedService[];
      is_active: boolean;
    }>,
  ) =>
    apiFetch<MembershipPlan>(
      `/clinics/${clinicId}/membership-plans/${planId}`,
      { method: "PATCH", body: JSON.stringify(body) },
    ),
  getPatientMembership: (patientId: string) =>
    apiFetch<PatientMembership | null>(`/patients/${patientId}/membership`),
  enrollPatientMembership: (patientId: string, planId: string) =>
    apiFetch<PatientMembership>(`/patients/${patientId}/membership`, {
      method: "POST",
      body: JSON.stringify({ plan_id: planId }),
    }),
  cancelPatientMembership: (patientId: string, membershipId: string) =>
    apiFetch<PatientMembership>(
      `/patients/${patientId}/membership/${membershipId}/cancel`,
      { method: "POST" },
    ),
  getOutstandingBalances: (clinicId: string) =>
    apiFetch<{ items: OutstandingBalanceEntry[]; total_outstanding: string }>(
      `/clinics/${clinicId}/outstanding-balances`,
    ),
  getRevenueSummary: (clinicId: string) =>
    apiFetch<RevenueSummary>(`/clinics/${clinicId}/revenue-summary`),
  getRevenueReport: (params: {
    from_date?: string;
    to_date?: string;
    group_by?: string;
    doctor_id?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params.from_date) qs.set("from_date", params.from_date);
    if (params.to_date) qs.set("to_date", params.to_date);
    if (params.group_by) qs.set("group_by", params.group_by);
    if (params.doctor_id) qs.set("doctor_id", params.doctor_id);
    const q = qs.toString();
    return apiFetch<ReportResponse>(`/reports/revenue${q ? `?${q}` : ""}`);
  },
  getAppointmentsReport: (params: {
    from_date?: string;
    to_date?: string;
    group_by?: string;
    doctor_id?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params.from_date) qs.set("from_date", params.from_date);
    if (params.to_date) qs.set("to_date", params.to_date);
    if (params.group_by) qs.set("group_by", params.group_by);
    if (params.doctor_id) qs.set("doctor_id", params.doctor_id);
    const q = qs.toString();
    return apiFetch<ReportResponse>(`/reports/appointments${q ? `?${q}` : ""}`);
  },
  getPatientGrowthReport: (params: {
    from_date?: string;
    to_date?: string;
    group_by?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params.from_date) qs.set("from_date", params.from_date);
    if (params.to_date) qs.set("to_date", params.to_date);
    if (params.group_by) qs.set("group_by", params.group_by);
    const q = qs.toString();
    return apiFetch<ReportResponse>(
      `/reports/patient-growth${q ? `?${q}` : ""}`,
    );
  },
  getTopDiagnosesReport: (params: {
    from_date?: string;
    to_date?: string;
    limit?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params.from_date) qs.set("from_date", params.from_date);
    if (params.to_date) qs.set("to_date", params.to_date);
    if (params.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return apiFetch<ReportResponse>(
      `/reports/top-diagnoses${q ? `?${q}` : ""}`,
    );
  },
  getNpsReport: (params: { from_date?: string; to_date?: string }) => {
    const qs = new URLSearchParams();
    if (params.from_date) qs.set("from_date", params.from_date);
    if (params.to_date) qs.set("to_date", params.to_date);
    const q = qs.toString();
    return apiFetch<NpsReportResponse>(`/reports/nps${q ? `?${q}` : ""}`);
  },
  listActivityLog: (
    clinicId: string,
    params: {
      page?: number;
      page_size?: number;
      actor_type?: string;
      action?: string;
      target_type?: string;
      target_id?: string;
      from_date?: string;
      to_date?: string;
      q?: string;
      sort?: string;
    } = {},
  ) => {
    const qs = new URLSearchParams();
    if (params.page) qs.set("page", String(params.page));
    if (params.page_size) qs.set("page_size", String(params.page_size));
    if (params.actor_type) qs.set("actor_type", params.actor_type);
    if (params.action) qs.set("action", params.action);
    if (params.target_type) qs.set("target_type", params.target_type);
    if (params.target_id) qs.set("target_id", params.target_id);
    if (params.from_date) qs.set("from_date", params.from_date);
    if (params.to_date) qs.set("to_date", params.to_date);
    if (params.q) qs.set("q", params.q);
    if (params.sort) qs.set("sort", params.sort);
    const q = qs.toString();
    return apiFetch<ActivityLogListResponse>(
      `/clinics/${clinicId}/activity-log${q ? `?${q}` : ""}`,
    );
  },
  receiptPdfUrl: (invoiceId: string) =>
    `${API_BASE}/invoices/${invoiceId}/receipt-pdf`,

  listDocumentTemplates: (clinicId: string) =>
    apiFetch<DocumentTemplate[]>(`/clinics/${clinicId}/document-templates`),
  createDocumentTemplate: (
    clinicId: string,
    body: {
      template_key: string;
      name: string;
      template_type: string;
      body_template: string;
      is_active?: boolean;
    },
  ) =>
    apiFetch<DocumentTemplate>(`/clinics/${clinicId}/document-templates`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchDocumentTemplate: (
    clinicId: string,
    templateId: string,
    body: Partial<{
      name: string;
      body_template: string;
      is_active: boolean;
    }>,
  ) =>
    apiFetch<DocumentTemplate>(
      `/clinics/${clinicId}/document-templates/${templateId}`,
      { method: "PATCH", body: JSON.stringify(body) },
    ),
  previewDocumentTemplate: (clinicId: string, body_template: string) =>
    apiFetch<{ placeholders: string[]; preview: string }>(
      `/clinics/${clinicId}/document-templates/preview`,
      { method: "POST", body: JSON.stringify({ body_template }) },
    ),
  listClinicalOrders: (patientId: string) =>
    apiFetch<
      Array<{
        id: string;
        order_type: string;
        name: string;
        status: string;
        result_summary: string | null;
        created_at: string;
      }>
    >(`/patients/${patientId}/orders`),
  createClinicalOrder: (
    patientId: string,
    body: { order_type: "lab" | "imaging"; name: string },
  ) =>
    apiFetch(`/patients/${patientId}/orders`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patchClinicalOrder: (
    patientId: string,
    orderId: string,
    body: { status?: string; result_summary?: string },
  ) =>
    apiFetch(`/patients/${patientId}/orders/${orderId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  patchDocument: (
    documentId: string,
    body: {
      referral_recipient?: string;
      referral_status?: string;
      referral_outcome?: string;
    },
  ) =>
    apiFetch<GeneratedDocument>(`/documents/${documentId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  listPatientDocuments: (patientId: string) =>
    apiFetch<{ items: GeneratedDocument[]; total: number }>(
      `/patients/${patientId}/documents`,
    ),
  createChartShare: (documentId: string) =>
    apiFetch<ChartShare>(`/documents/${documentId}/chart-share`, {
      method: "POST",
    }),
  createDocumentDraft: (
    patientId: string,
    body: {
      template_id: string;
      appointment_id?: string;
      referral_recipient?: string;
    },
  ) =>
    apiFetch<GeneratedDocument>(`/patients/${patientId}/documents`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  issueDocument: (documentId: string) =>
    apiFetch<GeneratedDocument>(`/documents/${documentId}/issue`, {
      method: "POST",
    }),

  getNotificationPreferences: (clinicId: string) =>
    apiFetch<NotificationPreferencesResponse>(
      `/clinics/${clinicId}/notification-preferences`,
    ),
  patchNotificationPreferences: (
    clinicId: string,
    body: Partial<{
      email_enabled: boolean;
      sms_enabled: boolean;
      whatsapp_enabled: boolean;
      confirmation_enabled: boolean;
      reminder_24h_enabled: boolean;
      reminder_2h_enabled: boolean;
      sender_name: string | null;
      chronic_condition_rules: Array<{
        condition: string;
        interval_months: number;
      }>;
      twilio_account_sid: string;
      twilio_auth_token: string;
      twilio_from_number: string;
      whatsapp_phone_number_id: string;
      whatsapp_access_token: string;
    }>,
  ) =>
    apiFetch<NotificationPreferencesResponse>(
      `/clinics/${clinicId}/notification-preferences`,
      { method: "PATCH", body: JSON.stringify(body) },
    ),
  listRecalls: (
    clinicId: string,
    params?: {
      status?: string;
      q?: string;
      page?: number;
      page_size?: number;
      sort?: string;
    },
  ) => {
    const search = new URLSearchParams();
    if (params?.status) search.set("status", params.status);
    if (params?.q) search.set("q", params.q);
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.sort) search.set("sort", params.sort);
    const qs = search.toString();
    return apiFetch<{
      items: PatientRecall[];
      total: number;
      page?: number;
      page_size?: number;
    }>(`/clinics/${clinicId}/recalls${qs ? `?${qs}` : ""}`);
  },
  listReminders: (status?: string) => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return apiFetch<
      Array<{
        id: string;
        appointment_id: string;
        patient_id: string;
        channel: string;
        reminder_type: string;
        scheduled_send_at: string;
        sent_at: string | null;
        status: string;
        patient_name?: string | null;
      }>
    >(`/reminders${qs}`);
  },
  searchReminders: (params?: {
    status?: string;
    q?: string;
    page?: number;
    page_size?: number;
    sort?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.status) search.set("status", params.status);
    if (params?.q) search.set("q", params.q);
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.sort) search.set("sort", params.sort);
    const qs = search.toString();
    return apiFetch<{
      items: Array<{
        id: string;
        appointment_id: string;
        patient_id: string;
        channel: string;
        reminder_type: string;
        scheduled_send_at: string;
        sent_at: string | null;
        status: string;
        patient_name?: string | null;
      }>;
      total: number;
      page: number;
      page_size: number;
    }>(`/reminders/search${qs ? `?${qs}` : ""}`);
  },
  retryReminder: (reminderId: string) =>
    apiFetch(`/reminders/${reminderId}/retry`, { method: "POST" }),
  patchRecall: (recallId: string, status: string) =>
    apiFetch<PatientRecall>(`/recalls/${recallId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  respondToReminder: (
    token: string,
    body: {
      action: "confirm" | "cancel" | "reschedule_request";
      message?: string;
    },
  ) =>
    apiFetch<{ status: string }>(`/public/reminders/${token}/respond`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  respondToNps: (token: string, body: { score: number; comment?: string }) =>
    apiFetch<PatientSurveyResponse>(`/public/nps/${token}/respond`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getPublicReferralChart: (token: string) =>
    apiFetch<{
      diagnoses: Array<{
        visit_date: string;
        doctor_name: string;
        diagnosis_primary: string | null;
        diagnosis_secondary: string[] | null;
        icd10_codes: string[] | null;
        follow_up_date: string | null;
      }>;
      vitals: Array<{
        recorded_at: string;
        height_cm: string | null;
        weight_kg: string | null;
        bmi: string | null;
        blood_pressure: string | null;
        temperature_c: string | null;
        heart_rate: number | null;
        respiratory_rate: number | null;
        spo2: number | null;
      }>;
    }>(`/public/referral-chart/${token}`),

  getPublicClinic: (slug: string) =>
    apiFetch<PublicClinicProfile>(`/public/clinics/${slug}`),
  getPublicSlots: (slug: string, doctorId: string, date: string) =>
    apiFetch<{
      slots: Array<{ scheduled_start: string; scheduled_end: string }>;
    }>(
      `/public/clinics/${slug}/available-slots?doctor_id=${doctorId}&date=${date}`,
    ),
  requestPublicAppointment: (slug: string, body: Record<string, unknown>) =>
    apiFetch<Appointment>(`/public/clinics/${slug}/appointment-requests`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listRecordings: (appointmentId: string) =>
    apiFetch<ConsultationRecording[]>(
      `/appointments/${appointmentId}/recordings`,
    ),
  createRecordingUpload: (
    appointmentId: string,
    body: {
      content_type: string;
      file_size_bytes: number;
      duration_seconds?: number | null;
    },
  ) =>
    apiFetch<RecordingUploadResponse>(
      `/appointments/${appointmentId}/recordings`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  submitRecording: (appointmentId: string, recordingId: string) =>
    apiFetch<ConsultationRecording>(
      `/appointments/${appointmentId}/recordings/${recordingId}/submit`,
      { method: "POST" },
    ),
  chartSearch: (clinicId: string, q: string) =>
    apiFetch<{ items: ChartSearchResult[] }>(
      `/clinics/${clinicId}/chart-search?q=${encodeURIComponent(q)}`,
    ),

  createAssistantConversation: () =>
    apiFetch<{ id: string }>("/assistant/conversations", { method: "POST" }),
  confirmAssistantAction: (actionId: string) =>
    apiFetch<{ status: string }>(`/assistant/actions/${actionId}/confirm`, {
      method: "POST",
    }),
  cancelAssistantAction: (actionId: string) =>
    apiFetch<{ status: string }>(`/assistant/actions/${actionId}/cancel`, {
      method: "POST",
    }),

  getVisitSummary: (appointmentId: string) =>
    apiFetch<VisitSummary | null>(
      `/appointments/${appointmentId}/visit-summary`,
    ),
  approveVisitSummary: (appointmentId: string, editedText?: string) =>
    apiFetch<VisitSummary>(
      `/appointments/${appointmentId}/visit-summary/approve`,
      {
        method: "POST",
        body: JSON.stringify({ edited_text: editedText ?? null }),
      },
    ),
  suppressVisitSummary: (appointmentId: string) =>
    apiFetch<VisitSummary>(
      `/appointments/${appointmentId}/visit-summary/suppress`,
      {
        method: "POST",
      },
    ),

  listStaffNotifications: (params?: {
    page?: number;
    page_size?: number;
    unread_only?: boolean;
  }) => {
    const search = new URLSearchParams();
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.unread_only) search.set("unread_only", "true");
    const qs = search.toString();
    return apiFetch<StaffNotificationListResponse>(
      `/notifications${qs ? `?${qs}` : ""}`,
    );
  },
  staffNotificationsUnreadCount: () =>
    apiFetch<{ unread_count: number; unread_capped: boolean }>(
      "/notifications/unread-count",
    ),
  markStaffNotificationRead: (notificationId: string) =>
    apiFetch<void>(`/notifications/${notificationId}/read`, { method: "POST" }),
  markAllStaffNotificationsRead: () =>
    apiFetch<{ marked: number }>("/notifications/read-all", { method: "POST" }),
  getStaffNotificationPrefs: () =>
    apiFetch<{ prefs: Record<string, Record<string, boolean>> }>(
      "/notifications/prefs",
    ),
  patchStaffNotificationPrefs: (
    prefs: Record<string, Record<string, boolean>>,
  ) =>
    apiFetch<{ prefs: Record<string, Record<string, boolean>> }>(
      "/notifications/prefs",
      { method: "PATCH", body: JSON.stringify({ prefs }) },
    ),
  registerPushSubscription: (body: {
    endpoint: string;
    keys: { p256dh: string; auth: string };
  }) =>
    apiFetch<{ id: string; endpoint: string }>(
      "/notifications/push-subscriptions",
      { method: "POST", body: JSON.stringify(body) },
    ),
  unregisterPushSubscription: (body: {
    endpoint: string;
    keys: { p256dh: string; auth: string };
  }) =>
    apiFetch<void>("/notifications/push-subscriptions", {
      method: "DELETE",
      body: JSON.stringify(body),
    }),
};

export type VisitSummary = {
  id: string;
  appointment_id: string;
  generated_text: string;
  generation_failed: boolean;
  edited_text: string | null;
  status: string;
  sent_at: string | null;
};

export type StaffNotification = {
  id: string;
  clinic_id: string;
  type: string;
  title: string;
  body: string | null;
  entity_type: string | null;
  entity_id: string | null;
  href: string | null;
  metadata: Record<string, unknown>;
  actor_user_id: string | null;
  created_at: string;
  is_read: boolean;
};

export type StaffNotificationListResponse = {
  items: StaffNotification[];
  total: number;
  page: number;
  page_size: number;
  unread_count: number;
  unread_capped: boolean;
};

export type PublicClinicProfile = {
  name: string;
  slug: string;
  address: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  working_hours: Record<
    string,
    { open: string; close: string; closed: boolean }
  > | null;
  holiday_dates: string[];
  default_appointment_duration_minutes: number;
  doctors: Array<{ id: string; specialty: string | null; full_name: string }>;
  services: Array<{ name: string; amount: string }>;
};
