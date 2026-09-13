const ACCESS_KEY = "dd_access_token";
const REFRESH_KEY = "dd_refresh_token";
const CLINIC_KEY = "dd_clinic_id";

const clinicListeners = new Set<() => void>();
let clinicSnapshot: string | null = null;

function storage() {
  if (typeof localStorage === "undefined") return null;
  return localStorage;
}

function readClinicId() {
  return storage()?.getItem(CLINIC_KEY) ?? null;
}

function syncClinicSnapshot() {
  clinicSnapshot = readClinicId();
}

function notifyClinicChange() {
  syncClinicSnapshot();
  clinicListeners.forEach((listener) => listener());
}

if (typeof window !== "undefined") {
  syncClinicSnapshot();
}

export function subscribeActiveClinic(onStoreChange: () => void) {
  clinicListeners.add(onStoreChange);
  return () => {
    clinicListeners.delete(onStoreChange);
  };
}

export function getActiveClinicSnapshot() {
  if (clinicSnapshot === null && typeof window !== "undefined") {
    syncClinicSnapshot();
  }
  return clinicSnapshot;
}

export function saveAuth(
  tokens: { access_token: string; refresh_token: string },
  clinicId: string,
) {
  storage()?.setItem(ACCESS_KEY, tokens.access_token);
  storage()?.setItem(REFRESH_KEY, tokens.refresh_token);
  const prev = readClinicId();
  storage()?.setItem(CLINIC_KEY, clinicId);
  if (prev !== clinicId) {
    notifyClinicChange();
  }
}

export function clearAuth() {
  storage()?.removeItem(ACCESS_KEY);
  storage()?.removeItem(REFRESH_KEY);
  storage()?.removeItem(CLINIC_KEY);
  if (typeof sessionStorage !== "undefined") {
    sessionStorage.removeItem("dd_impersonating");
  }
  notifyClinicChange();
}

export function saveSupportSession(accessToken: string, clinicId: string) {
  storage()?.setItem(ACCESS_KEY, accessToken);
  storage()?.removeItem(REFRESH_KEY);
  const prev = readClinicId();
  storage()?.setItem(CLINIC_KEY, clinicId);
  sessionStorage.setItem("dd_impersonating", "1");
  if (prev !== clinicId) {
    notifyClinicChange();
  }
}

export function isImpersonating() {
  return (
    typeof sessionStorage !== "undefined" &&
    sessionStorage.getItem("dd_impersonating") === "1"
  );
}

export function getAccessToken() {
  return storage()?.getItem(ACCESS_KEY) ?? null;
}

export function getRefreshToken() {
  return storage()?.getItem(REFRESH_KEY) ?? null;
}

export function getClinicId() {
  return readClinicId();
}

export function setActiveClinic(clinicId: string) {
  const prev = readClinicId();
  storage()?.setItem(CLINIC_KEY, clinicId);
  if (prev !== clinicId) {
    notifyClinicChange();
  }
}

/** True during SSR where localStorage is unavailable — skip auth redirects until the client runs. */
export function shouldDeferAuthRedirect() {
  return typeof window === "undefined";
}

export function isAuthenticated() {
  return Boolean(getAccessToken());
}
