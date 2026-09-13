const TOKEN_KEY = "dd_patient_access_token";
const PATIENT_ID_KEY = "dd_patient_id";
const CLINIC_ID_KEY = "dd_patient_clinic_id";
const CONSENT_KEY = "dd_patient_portal_consent_ack";

function storage() {
  if (typeof localStorage === "undefined") return null;
  return localStorage;
}

export function savePatientAuth(
  accessToken: string,
  patientId: string,
  clinicId: string,
) {
  storage()?.setItem(TOKEN_KEY, accessToken);
  storage()?.setItem(PATIENT_ID_KEY, patientId);
  storage()?.setItem(CLINIC_ID_KEY, clinicId);
}

export function clearPatientAuth() {
  storage()?.removeItem(TOKEN_KEY);
  storage()?.removeItem(PATIENT_ID_KEY);
  storage()?.removeItem(CLINIC_ID_KEY);
}

export function getPatientAccessToken() {
  return storage()?.getItem(TOKEN_KEY) ?? null;
}

export function isPatientAuthenticated() {
  return Boolean(getPatientAccessToken());
}

/** True during SSR where localStorage is unavailable — skip auth redirects until the client runs. */
export function shouldDeferPortalAuthRedirect() {
  return typeof window === "undefined";
}

export function hasAckedPortalConsent() {
  return storage()?.getItem(CONSENT_KEY) === "1";
}

export function ackPortalConsent() {
  storage()?.setItem(CONSENT_KEY, "1");
}
