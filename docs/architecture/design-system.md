# Design system reference (historical TailAdmin audit)

**Status: historical audit.** Do not implement from this file. Authoritative spec: [`design-language.md`](./design-language.md). Principles: [`DESIGN.md`](../../DESIGN.md). Pass/fail rules: `.cursor/rules/anti-slop-design.mdc`.

This document records what was extracted from [react-demo.tailadmin.com](https://react-demo.tailadmin.com/) and what shipped when DoctorDesk matched that demo on request (2026-09-10). The professional design overhaul (Phases 42–47) exists because that match left template tells in the product.

**Revoked decisions in this file:**

- **§3.2 / §11 brand ramp.** Matching TailAdmin's literal indigo is no longer the product direction. Hue is unratified; indigo/violet is off the table. See `design-language.md` §3.
- **§12 "every page carries a description."** `ui-minimal-copy.mdc` wins. Restating the title is a B7 fail. `PageHeader` `description` is optional.
- **§11.2 "design-quality hook."** No such hook exists in `.cursor/hooks/`. Design review is the `design-review` skill + `pnpm run check:design-slop`.

Kept as evidence: literal TailAdmin token tables, component inventory, and the extraction method (`.agent/skills/design-system-extraction/SKILL.md`).

Source: TailAdmin React free tier. Extracted via live browser inspection (computed styles) + static analysis of the compiled CSS/JS bundle, not visual guessing.

## 1. Stack identified

| Layer            | TailAdmin uses                                                                  | Verdict for DoctorDesk                                                                                                            |
| ---------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| CSS framework    | Tailwind CSS v4.0.15 (`@theme` tokens, oklch colors)                            | Already our stack (`tech-stack.md`) — no change                                                                                   |
| Components       | Fully custom (no shadcn/Radix/Headless UI found in bundle)                      | We use shadcn/ui — port _tokens_, not component code                                                                              |
| Charts           | ApexCharts (`react-apexcharts`), 226 references in bundle                       | Good fit, MIT-equivalent free license, no chart lib decided yet — recommend                                                       |
| Calendar         | FullCalendar (`@fullcalendar/*`)                                                | `tech-stack.md` already lists FullCalendar resource view as an option — this corroborates it                                      |
| Date picker      | flatpickr                                                                       | Shipped as `DatePicker` / `DateRangePicker` / `Calendar` (`react-day-picker` v9) + `TimePicker` — TailAdmin tokens, not flatpickr |
| Vector/world map | `@react-jvectormap` (jQuery-based) + MapLibre GL (`maplibregl` keyframes found) | Not relevant — DoctorDesk has no maps feature                                                                                     |
| Carousel         | Swiper                                                                          | Not currently needed                                                                                                              |
| Custom scrollbar | SimpleBar                                                                       | Optional polish, not required                                                                                                     |
| Icons            | Hand-built inline SVGs (no icon library in bundle)                              | Keep our existing decision: **Lucide**                                                                                            |
| Toasts           | None found (their "Notification" page is static markup, not a real toast lib)   | Keep our existing decision: **Sonner**                                                                                            |
| Analytics/misc   | Cloudflare Zaraz + Cloudflare Insights beacon                                   | Not relevant to app design                                                                                                        |

All libraries above ship under permissive OSS licenses (ApexCharts: MIT, FullCalendar core: MIT, flatpickr: MIT, Swiper: MIT, SimpleBar: MIT). No GPL/AGPL/commercial-only dependency detected.

## 2. Typography

| Token          | Value                                                                                                                                                                  |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Font family    | **IBM Plex Sans** (DoctorDesk source of truth). TailAdmin's demo used Outfit; we do not. Loaded in `__root.tsx` and set as `--font-sans` in `apps/web/src/styles.css`. |
| Fallback stack | `"IBM Plex Sans Fallback", ui-sans-serif, system-ui, -apple-system, sans-serif`                                                                                        |
| Monospace      | **IBM Plex Mono** (`--font-mono`) for IDs, timestamps, audit/document preview                                                                                          |
| Weights used   | 400 (normal), 500 (medium), 600 (semibold), 700 (bold)                                                                                                                 |

Type scale (`--text-*` tokens, Tailwind v4 defaults — unmodified):

| Token       | Size            | Line-height           |
| ----------- | --------------- | --------------------- |
| `text-xs`   | 12px (0.75rem)  | `calc(1/0.75)` ≈ 1.33 |
| `text-sm`   | 14px (0.875rem) | ≈ 1.43                |
| `text-base` | 16px (1rem)     | 1.5                   |
| `text-lg`   | 18px (1.125rem) | ≈ 1.56                |
| `text-xl`   | 20px (1.25rem)  | 1.4                   |
| `text-2xl`  | 24px (1.5rem)   | ≈ 1.33                |
| `text-3xl`  | 30px (1.875rem) | 1.2                   |

Custom marketing/display scale (`--text-theme-*`, `--text-title-*`) exists for landing-page-style headings (48–72px). **Skip these for DoctorDesk** — a clinic dashboard has no marketing hero sections; reuse the standard scale up to `2xl`/`3xl` for page titles at most.

**DoctorDesk decision:** keep Outfit as a candidate but it is not mandatory — `DESIGN.md` currently says "system stack or Inter via `font-sans`." Outfit is a clean, legible geometric sans that would work equally well for a clinical UI and is free (OFL license via Google Fonts). Recommend picking **one** of Inter or Outfit and stop revisiting; either satisfies "clarity over decoration."

## 3. Color system

### 3.1 Neutral ramp (ready to reuse as-is — this is Tailwind's own gray scale)

| Token                | Hex                                   |
| -------------------- | ------------------------------------- |
| `gray-50`            | `#f9fafb`                             |
| `gray-100`           | `#f2f4f7`                             |
| `gray-200`           | `#e4e7ec`                             |
| `gray-300`           | `#d0d5dd`                             |
| `gray-400`           | `#98a2b3`                             |
| `gray-500`           | `#667085`                             |
| `gray-600`           | `#475467`                             |
| `gray-700`           | `#344054`                             |
| `gray-800`           | `#1d2939`                             |
| `gray-900` / `black` | `#101828`                             |
| `gray-950`           | `#0c111d`                             |
| `gray-dark`          | `#1a2231` (dark-mode surface variant) |

This is exactly the "calm neutrals, white/slate surfaces" DoctorDesk's `DESIGN.md` already asks for. **Adopt directly.**

### 3.2 Brand/primary ramp (adopted verbatim — literal TailAdmin hex values)

**Superseded 2026-09-10.** The original decision below (reject the indigo hue, ship a clinical teal instead) was overridden by an explicit request to match `react-demo.tailadmin.com` exactly, including the primary color and dark-mode surfaces. DoctorDesk now ships TailAdmin's literal 12-step brand ramp (`25`→`950`) in `apps/web/src/styles.css`, unchanged:

| Step | Hex       | Step | Hex       |
| ---- | --------- | ---- | --------- |
| 25   | `#f2f7ff` | 600  | `#3641f5` |
| 50   | `#ecf3ff` | 700  | `#2a31d8` |
| 100  | `#dde9ff` | 800  | `#252dae` |
| 200  | `#c2d6ff` | 900  | `#262e89` |
| 300  | `#9cb9ff` | 950  | `#161950` |
| 400  | `#7592ff` |      |           |
| 500  | `#465fff` |      |           |

`--color-primary` / `--ring` / active nav / primary buttons all resolve to `brand-500 #465fff` in both light and dark mode (TailAdmin does not shift the primary hue per theme — it's vivid enough to read on both backgrounds).

~~Original (superseded) text: TailAdmin's primary is a vivid indigo-blue... generate an equivalent ramp around a clinical teal-blue hue... Do not import TailAdmin's literal brand hex values.~~

### 3.3 Semantic ramps (adopt directly — these are near-universal conventions, not "TailAdmin branding")

| Role              | 50        | 500       | 600       | 700       |
| ----------------- | --------- | --------- | --------- | --------- |
| Success           | `#ecfdf3` | `#12b76a` | `#039855` | `#027a48` |
| Warning           | `#fffaeb` | `#f79009` | `#dc6803` | `#b54708` |
| Error             | `#fef3f2` | `#f04438` | `#d92d20` | `#b42318` |
| Info (blue-light) | `#f0f9ff` | `#0ba5ec` | `#0086c9` | —         |

These map cleanly onto DoctorDesk's existing status-color intents (`DESIGN.md`):

| DoctorDesk status   | Suggested semantic token                                 |
| ------------------- | -------------------------------------------------------- |
| Scheduled           | `gray-*` (neutral)                                       |
| Confirmed           | brand/primary (new teal ramp)                            |
| Arrived             | `warning-*`                                              |
| In Consultation     | brand/primary                                            |
| Completed           | `success-*`                                              |
| Cancelled / No Show | `gray-*` (muted) or `error-*` for Cancelled specifically |

### 3.4 Dark mode strategy

Class-based, not `prefers-color-scheme`-only: `document.documentElement` gets a `.dark` class. Preference is `light` | `dark` | `system` in `localStorage` (`dd-theme`). Tailwind `dark:` variants follow the class.

**DoctorDesk (implemented):** same pattern as kame-homes. `lib/theme/preferences.ts` owns read/persist/resolve/apply. `ThemeProvider` listens for OS changes when preference is `system`. An inline FOUC script in `__root.tsx` sets `.dark` before paint. Inside the dashboard, the choice lives in the header account menu as a Light / Dark / System radio group; auth, landing, onboarding, and public booking use the icon toggle. Charts and toasts follow `resolvedTheme`. Front-desk tablets need an explicit, persistent choice, not OS-only detection.

activity-log: N/A — theme preference is stored in the browser (`dd-theme` in `localStorage`). It does not mutate clinic or patient records.

Measured dark-mode surfaces (via `getComputedStyle` on the live site):

| Element          | Dark background                                                                                                  |
| ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| Sidebar / header | `rgb(16,24,40)` = `gray-900`                                                                                     |
| Card             | `white/3%` (`oklab(... / 0.03)` — i.e. `bg-white/[0.03]` over the dark page background, not a flat second color) |
| Page background  | same `gray-900` as sidebar/header (no separate "canvas" tone)                                                    |

## 4. Spacing & layout

| Token                | Value                                                                                                                              |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Base spacing unit    | `0.25rem` (4px) — standard Tailwind v4, unmodified                                                                                 |
| Sidebar width        | 290px (measured)                                                                                                                   |
| Header height        | 64px (`h-16`) in DoctorDesk (`AppHeader`); TailAdmin measured 77px                                                                 |
| Page content padding | `p-4` (16px) / `sm:p-6` (24px) on `DashboardShell` `<main>` — every dashboard page inherits this; do not re-apply on feature pages |
| Page content width   | `PageContainer` (`components/layout/PageContainer.tsx`) — `default` = `max-w-6xl`, `narrow` = `max-w-2xl`, both `mx-auto`          |
| Page title → content | `mb-4` / `sm:mb-6` on `PageHeader` — same 16/24px rhythm as the page gutter                                                        |
| Card padding         | `20px 16px` typ. (`py-5 px-4`), scales to `p-6` on larger cards                                                                    |
| Card radius          | 16px (`rounded-2xl`) for dashboard stat/chart cards                                                                                |
| Container breakpoint | `2xl` = 1536px (only custom breakpoint override; all others are Tailwind defaults)                                                 |

Grid rhythm observed across dashboard: 16px/24px gaps between cards, consistent with the 4px base scale — no arbitrary pixel values found outside the token system. This "no magic numbers" discipline is worth adopting regardless of brand.

## 5. Border radius scale

Tailwind v4 defaults, unmodified — safe to adopt as-is:

| Token         | Value                                   |
| ------------- | --------------------------------------- |
| `radius-xs`   | 2px                                     |
| `radius-sm`   | 4px                                     |
| `radius-md`   | 6px                                     |
| `radius-lg`   | 8px                                     |
| `radius-xl`   | 12px                                    |
| `radius-2xl`  | 16px                                    |
| `radius-3xl`  | 24px                                    |
| `radius-full` | pill (huge value, effectively `9999px`) |

Observed usage: buttons/inputs → `rounded-lg` (8px); cards/panels → `rounded-2xl` (16px); avatars/pills/badges → `rounded-full`.

## 6. Shadows (elevation scale)

Custom named scale layered on top of Tailwind's shadow utilities — all very subtle (low-opacity, tight-radius), consistent with a data-dense dashboard rather than a marketing site:

| Token             | `box-shadow`                                                                   |
| ----------------- | ------------------------------------------------------------------------------ |
| `shadow-theme-xs` | `0px 1px 2px 0px rgba(16,24,40,0.05)`                                          |
| `shadow-theme-sm` | `0px 1px 3px 0px rgba(16,24,40,0.10), 0px 1px 2px 0px rgba(16,24,40,0.06)`     |
| `shadow-theme-md` | `0px 4px 8px -2px rgba(16,24,40,0.10), 0px 2px 4px -2px rgba(16,24,40,0.06)`   |
| `shadow-theme-lg` | `0px 12px 16px -4px rgba(16,24,40,0.08), 0px 4px 6px -2px rgba(16,24,40,0.03)` |

Measured on a real primary button: `0 1px 2px 0 rgba(16,24,40,0.05)` (i.e. `shadow-theme-xs`) — buttons get the lightest tier, cards get `sm`/`md`, modals/popovers get `lg`. **Adopt this exact 4-tier scale** — it is brand-neutral (uses the gray-900 base color for the shadow tint, not a brand hue) and appropriate for a dense clinical UI that shouldn't look "flashy."

## 7. Motion / animation

| Token                       | Value                                                                                                                                                 |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Default transition duration | Micro **0.15s**; transition **0.28s**; page **0.3s** (`apps/web/src/lib/motion.ts`)                                                                   |
| Default easing              | Micro: `cubic-bezier(0.4, 0, 0.2, 1)` (`ease-theme`). Transition/page: `cubic-bezier(0.22, 1, 0.36, 1)` (`ease-out-quart`) or damped spring for pills |
| Date picker enter           | Radix Popover + `Calendar`. Sliding pills use `framer-motion` + `SLIDING_PILL_SPRING` (reduced-motion: instant)                                       |

Page-level dashboard navigation uses `PageTransition` (translate+fade, no cross-fade). `prefers-reduced-motion` disables animation. No GSAP, no hospitality bounce/confetti. **`framer-motion` is an explicit frontend dependency** for pill, list stagger, and page transition only.

## 8. Component inventory (what TailAdmin ships, mapped to DoctorDesk needs)

| Component family                         | Variants/states observed                                                                                                                                                                    | DoctorDesk relevance                                                                                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Buttons                                  | primary / secondary(outline) × sm(44px)/md(48px) × with-icon-left/right; shadow-theme-xs; `rounded-lg`                                                                                      | Direct match — primary actions, confirm/cancel                                                                                                          |
| Cards                                    | with image, horizontal, with link, with icon, plain stat card                                                                                                                               | Stat cards (dashboard KPIs), patient/appointment cards                                                                                                  |
| Badges                                   | solid + light-fill variants per semantic color                                                                                                                                              | Appointment/visit status chips                                                                                                                          |
| Alerts                                   | success/warning/error/info, with optional "Learn more" link                                                                                                                                 | Form validation banners, AI Tier-2 confirm context                                                                                                      |
| Avatar                                   | single, group/stacked (used in table "Team" column)                                                                                                                                         | Patient/doctor avatars, assigned-staff stacks                                                                                                           |
| Tables                                   | Shared `ManagedList` chrome: live search, filters, sort, per-page (25/50/100), Table / List / Grid (Calendar on appointments). Phone defaults to List.                                      | Appointments, patients, invoices, claims, activity log, recalls, reminders, tenants                                                                     |
| Forms                                    | text/select/password/date/time/tel/textarea, input groups (icon-prefixed), validation states (error/success/disabled), checkbox/radio/toggle, searchable lazy-loading picker, file dropzone | Patient intake, appointment forms, prescriptions                                                                                                        |
| Modals / Dropdowns / Popovers / Tooltips | custom-built (no headless lib)                                                                                                                                                              | Confirm dialogs, AI Tier-2 confirm cards, context menus                                                                                                 |
| Tabs / Breadcrumb / Pagination           | standard patterns                                                                                                                                                                           | Patient detail tabs (Overview/Visits/Billing), nav breadcrumbs                                                                                          |
| Charts                                   | line, bar, pie, radar, radial (ApexCharts)                                                                                                                                                  | Revenue/appointments trend, demographics                                                                                                                |
| Calendar                                 | month/week/day resource view (FullCalendar)                                                                                                                                                 | Appointment scheduling calendar                                                                                                                         |
| Kanban                                   | task board                                                                                                                                                                                  | Shipped: `KanbanBoard` + waiting room (`@dnd-kit/core`) on desktop; mobile keeps swipe                                                                  |
| File manager                             | grid/list file browser                                                                                                                                                                      | Not currently in MVP scope (documents live under patient records, not a general file manager) — skip                                                    |
| Error/empty states                       | 404/500/503, coming-soon, maintenance, success                                                                                                                                              | Reuse the _pattern_ (icon + bold "ERROR" + one short line + single CTA) but rewrite all copy per `human-copy.mdc` — TailAdmin's copy is template filler |
| Auth pages                               | sign in/up, reset password, two-step verification, "purchase plan"                                                                                                                          | Sign-in/reset relevant; no "purchase plan" — DoctorDesk has no per-seat marketing paywall UI                                                            |

## 9. What to explicitly reject

- ~~Brand hue — TailAdmin's indigo/violet `brand-500 #465fff`.~~ **Superseded (§3.2)** — this hue is now adopted verbatim.
- **Decorative stock photography** in cards ("PUNCH TODAY IN THE FACE" desk photos) — marketing-template filler, not appropriate anywhere in a clinical dashboard.
- **Lorem-ipsum / marketing microcopy** ("Read more", "Learn more", promotional card blurbs) — violates `ui-minimal-copy.mdc` and `human-copy.mdc` outright; every string must be rewritten for the actual clinical action.
- **"NEW" nav badges / upsell nav items** (AI Assistant, Sales, Finance marked `new`, "Purchase Plan" auth page) — that's the paid-tier template upsell pattern, not applicable.
- **General file manager** — outside current MVP scope; do not scaffold speculative UI for it. (Waiting-room kanban is in scope.)
- **Display type scale** (48–72px marketing headings) — no marketing hero surfaces exist in the product.

## 10. Draft Tailwind v4 `@theme` starter (illustrative, not final)

Adjust the brand ramp's actual hue before use; everything else below is taken directly from sections 2–7 above and is ready to use.

```css
@theme {
  /* radius */
  --radius-xs: 0.125rem;
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  --radius-2xl: 1rem;
  --radius-3xl: 1.5rem;

  /* motion */
  --default-transition-duration: 0.15s;
  --default-transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);

  /* shadows */
  --shadow-theme-xs: 0px 1px 2px 0px rgba(16, 24, 40, 0.05);
  --shadow-theme-sm:
    0px 1px 3px 0px rgba(16, 24, 40, 0.1),
    0px 1px 2px 0px rgba(16, 24, 40, 0.06);
  --shadow-theme-md:
    0px 4px 8px -2px rgba(16, 24, 40, 0.1),
    0px 2px 4px -2px rgba(16, 24, 40, 0.06);
  --shadow-theme-lg:
    0px 12px 16px -4px rgba(16, 24, 40, 0.08),
    0px 4px 6px -2px rgba(16, 24, 40, 0.03);

  /* neutrals: adopt Tailwind gray scale as-is (see §3.1) */

  /* brand: placeholder — replace with clinical teal-blue 50-950 ramp */
  --color-brand-500: #0f9b8e; /* placeholder teal, not final — needs design pass */
}
```

## 11. Open decisions for the team

1. ~~Final brand teal-blue hex ramp (50–950)~~ — **re-resolved 2026-09-10.** The teal ramp shipped in an earlier pass was replaced with TailAdmin's literal indigo-blue ramp (`--color-brand-25`→`950`, see §3.2) at explicit user request to match the reference site's primary color and dark theme exactly. Semantic ramps (success/warning/error/info) were also swapped to TailAdmin's literal full 12-step values (previously a partial custom ramp). Dark-mode surfaces now mirror TailAdmin's measured tones: page/sidebar/header `#101828` (gray-900), card `rgba(255,255,255,0.03)` over that background with a `gray-800` border, popover/dropdown `#252d3a`, active-nav tint `color-mix(... brand-500 12% ...)`.
2. ~~Inter vs. Outfit as the UI font~~ — **resolved differently.** Neither shipped; the design-quality hook flagged Inter as an overused default, and Outfit was never wired up. **IBM Plex Sans** (UI text) + **IBM Plex Mono** (numeric/code contexts) shipped instead — distinctive, still a calm clinical sans, loaded via Google Fonts in `__root.tsx`. Update `DESIGN.md` if it still says "system stack or Inter."
3. Confirm ApexCharts + FullCalendar as the chart/calendar libraries — **resolved.** Both shipped (`components/charts/AppointmentsTrendChart.tsx`, `features/appointments/calendar/`). Date/time fields use `DatePicker` + `TimePicker` (`react-day-picker` v9, class `dd-datepicker`) rather than native `<input type="date">` or flatpickr. Appointment month/week/day views stay on FullCalendar.

## 12. Implementation notes (post-rollout)

- Base primitives: `apps/web/src/components/ui/*.tsx` — shadcn/ui pattern (Radix + `cva` + `cn()`), not TailAdmin's component code. Includes calendar/date-picker/date-range-picker/time-picker, progress, stepper, custom file dropzones (browse + drag, hidden native input), sliding tabs/pills, radio-group, scroll-area, alert-dialog, button-group, slider/number-slider, combobox, brand-color-field, kanban-board, checkbox display helper, interactive card variant, plus button, card, badge, input, label, textarea, select, dialog, sheet (`hideClose` / `showHandle` / `overlayClassName`), `responsive-modal`, dropdown-menu, tabs, tooltip, avatar, separator, switch, popover, table, skeleton, breadcrumb, checkbox, sonner, form, collapsible, search-input, entity-row, staggered-list, rich-text-editor (TipTap), template-placeholders, `EmptyState` / `ErrorState`. High-cardinality entity pickers use server search plus incremental 25-row pages; they never render the full dataset. Form labels/errors live in `components/forms/`; shared placeholders in `lib/formPlaceholders.ts`. Document letter tokens live in `lib/documentTemplatePlaceholders.ts`.
- Every from/to filter uses `DateRangePicker`, never two `DatePicker`s: appointments, invoices, activity log, and reports. It shows two months (one below `sm`), applies on the second click, and paints the interval through `.rdp-range_start` / `.rdp-range_middle` / `.rdp-range_end` in `styles.css`. It must pass `onSelect` to `react-day-picker`, which only honors `selected` as controlled state when that handler exists. `DatePicker` stays for single dates (birth date, follow-up, booking, accreditation validity); no screen uses a native `<input type="date">`.
- TanStack Query defaults use a 30-second stale window, a 10-minute inactive cache, one read retry, and no automatic mutation retries. Paginated lists retain the previous page while the next page loads. Mutations invalidate resource-key prefixes so all affected filters and pages refresh together.
- Pointer contract: `@layer base` in `styles.css` sets `cursor: pointer` on buttons and interactive ARIA roles; disabled states use `cursor-not-allowed`. Menu/select items use `cursor-pointer`, not shadcn's default arrow cursor.
- App shell: `components/layout/AppSidebar.tsx` (desktop `lg+` only; brand + collapse toggle in the top row, `localStorage`-persisted collapse, clinic switcher, nav — no footer section), `AppHeader.tsx` (command palette trigger, `NotificationBell`, account menu holding Settings / Platform / theme choice / Sign out), `DashboardShell.tsx` composes both plus `BottomTabBar` / `MobileMoreSheet` below `lg`, `PageTransition`, and the AI assistant launcher. Theme selection lives in one place only: the account menu (Light / Dark / System radio group). Dashboard page gutter lives on `<main>` (`p-4 sm:p-6` plus bottom-tab inset below `lg`); `PageHeader` owns the title-to-content gap (`mb-4 sm:mb-6`). Feature pages must not add a second `p-4 sm:p-6`.
- Page width and alignment: `components/layout/PageContainer.tsx` is the only place page width is declared (`default` = `max-w-6xl` for lists, boards, hubs, settings, and detail pages; `narrow` = `max-w-2xl` for standalone create/edit forms). Content inside a `default` container is full width; nested `max-w-xl` / `max-w-3xl` wrappers are not allowed. Pages whose root element already exists use the `pageContainerClass()` helper from the same module. Tabbed sections use `SectionHubShell`, which takes one `SectionHub` descriptor (`title` + `description` + `tabs`, defined in `nav-config.ts`) and owns the container, the `<h1>`, the description, and the tab bar. The visual order is title and description, tabs, then page content, all sharing one left edge. Rules: exactly one `<h1>` per page and every page carries a description; a hub's title equals its sidebar nav label and is **fixed**, so switching tabs changes only the content below the tab bar; a tab page renders **no** heading of its own and passes its primary buttons through `SectionHeaderActions`, which portals them into the fixed header; a page nested in `SectionHubShell` or `SettingsLayout` must not add a container of its own; hub tabs are applied per child route, so `/appointments/new`, the SOAP editor, and claim detail do not inherit a section's tab switcher. `PageHeader`'s `subNav` slot renders any secondary nav under the title (used by the shell and by `PatientDetailSubNav`).
- Motion: `apps/web/src/lib/motion.ts` + `framer-motion` for the sliding pill, command-palette stagger, and dashboard `PageTransition`. `PageTransition` is keyed by `pageTransitionKey(pathname)`, which collapses sibling tabs of one section to a single key so a tab click swaps content without re-animating the fixed header. CSS keyframes `fade-up` / `scale-in` / `slide-in-from-bottom` / `stage-in-forward` in `styles.css`. `.native-press` / `.interactive-lift` utilities. All new motion is `prefers-reduced-motion` safe.
- Skeletons: `apps/web/src/components/skeletons/PageSkeletons.tsx` (per-page markup). Swipe-to-reveal: `components/mobile/SwipeRevealRow.tsx` on appointment rows and waiting-room cards below `lg`.
- FullCalendar and ApexCharts both needed hand-authored theme bridges rather than pure `@theme` tokens: FullCalendar via `.dd-calendar` CSS-variable overrides in `styles.css`; ApexCharts via runtime options (no CSS var support) plus a `ClientOnly` wrapper (`components/charts/AppointmentsTrendChart.tsx`) since it touches `window` during SSR. Date picker chrome is `.dd-datepicker`; toasts are `.dd-toast` (hex CSS vars, status as border color).
- Every feature page under `apps/web/src/features/*/pages/` (patients, appointments, waiting room, SOAP, billing, settings, reports, chart search, recalls, audit log, documents, prescriptions, public booking, reminders) was rebuilt on these primitives; onboarding and auth (`login`/`register`) share `AuthLayout`. Onboarding uses `Stepper`; reports use `SegmentedControl` + `Progress`; signature/receipt uploads use the dropzone primitives.
- Shadow scale (§6) and radius scale (§5) were adopted essentially as specified. The brand ramp (§3.2) and semantic ramps (§3.3) were adapted with new hex values, not copied from TailAdmin.
