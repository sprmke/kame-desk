export const THEME_STORAGE_KEY = "dd-theme";

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

const LIGHT_THEME_COLOR = "#f9fafb";
const DARK_THEME_COLOR = "#101828";

function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function resolveTheme(preference: ThemePreference): ResolvedTheme {
  if (preference === "system") return getSystemTheme();
  return preference;
}

export function readStoredTheme(): ThemePreference {
  if (typeof window === "undefined") return "system";
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "light" || stored === "dark" || stored === "system") {
    return stored;
  }
  return "system";
}

export function persistTheme(preference: ThemePreference) {
  localStorage.setItem(THEME_STORAGE_KEY, preference);
}

function syncThemeColorMeta(resolved: ResolvedTheme) {
  const content = resolved === "dark" ? DARK_THEME_COLOR : LIGHT_THEME_COLOR;
  document.querySelectorAll('meta[name="theme-color"]').forEach((node) => {
    if (node instanceof HTMLMetaElement && !node.media) {
      node.content = content;
    }
  });
}

export function applyThemeClass(resolved: ResolvedTheme) {
  const root = document.documentElement;
  root.classList.toggle("dark", resolved === "dark");
  root.style.colorScheme = resolved;
  syncThemeColorMeta(resolved);
}

/** Inline script to set `.dark` before first paint (no FOUC). */
export const themeInitScript = `
(function() {
  try {
    var stored = localStorage.getItem('${THEME_STORAGE_KEY}');
    var resolved = stored === 'light' || stored === 'dark'
      ? stored
      : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', resolved === 'dark');
    document.documentElement.style.colorScheme = resolved;
    var color = resolved === 'dark' ? '#101828' : '#f9fafb';
    document.querySelectorAll('meta[name="theme-color"]').forEach(function (node) {
      if (!node.getAttribute('media')) node.setAttribute('content', color);
    });
  } catch (e) {}
})();
`;
