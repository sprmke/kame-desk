# Professional design overhaul (anti-slop)

**Status:** In progress. Phases 42–43 done (waiting-room Kanban retained; brand hue not ratified; anti-slop rule/skill/checker/harness shipped). Next: Phase 44 Hierarchy and density. Tracker: [`docs/workflow/in-progress/professional-design-overhaul-anti-slop.md`](../in-progress/professional-design-overhaul-anti-slop.md). Phases 44–47 not started.
**Scope:** Presentation layer of `apps/web` + the agent rules/skills/docs that govern it. No API, schema, or business-logic changes.
**Goal:** The product should read as designed by a person who cares, working in a clinical domain, and not as a Tailwind admin template with a healthcare noun substituted in.

activity-log: N/A — presentation-only plan, no clinic/patient/appointment writes.

---

## 1. The diagnosis

The complaint ("looks AI-generated, sloppy, like a normal Tailwind/shadcn app") is correct, and it is not a collection of small polish misses. There is one root cause with five downstream symptoms.

### 1.1 Root cause: the design system was extracted, not designed

`docs/architecture/design-system.md` records the method honestly: the token set was lifted from `react-demo.tailadmin.com` by inspecting computed styles, then adopted. §3.2 was explicitly _superseded_ to adopt TailAdmin's brand ramp verbatim, and `apps/web/src/styles.css:14` says so in a comment:

```14:26:apps/web/src/styles.css
  /* Brand — matches TailAdmin's indigo-blue ramp exactly (react-demo.tailadmin.com) */
  --color-brand-25: #f2f7ff;
  --color-brand-50: #ecf3ff;
  --color-brand-100: #dde9ff;
  --color-brand-200: #c2d6ff;
  --color-brand-300: #9cb9ff;
  --color-brand-400: #7592ff;
  --color-brand-500: #465fff;
```

`#465fff` is a vivid indigo-violet. It is the same family as Tailwind's default `indigo-500`, shadcn's default primary, Bootstrap's `primary`, and roughly every SaaS template shipped since 2021. The neutral ramp is Tailwind's own gray scale, unmodified (§3.1: "Adopt directly"). The type scale is Tailwind's defaults, unmodified (§2: "unmodified"). The radius scale is Tailwind's defaults. The shadow scale is TailAdmin's.

So: every single visual decision that would normally carry brand identity was inherited from a generic admin template. The app looks like a generic admin template because, at the token level, it _is_ one. No amount of component polish fixes this, and the prior UI pass (`docs/workflow/done/ui-ux-refinement-native-mobile.md`) could not have fixed it because it was scoped to motion, skeletons, sheets, and press states, all downstream of tokens.

Worse, the doc's own §9 "What to explicitly reject" correctly identified the brand skin as the thing to reject, and then §3.2/§11 reversed that decision. The reasoning recorded for the reversal is "explicit request to match `react-demo.tailadmin.com` exactly." That request needs to be formally revoked as part of this plan, or every future agent session will re-apply it.

### 1.2 Symptom: card soup, no hierarchy

There is one `Card` and every surface is it. 99 `<Card>` usages across `apps/web/src`, all resolving to the same shell:

```5:6:apps/web/src/components/ui/card.tsx
const cardVariants = cva(
  "rounded-2xl border border-border bg-card text-card-foreground shadow-theme-xs",
```

Uniform 16px radius, uniform 1px border, uniform `shadow-theme-xs`, and `CardHeader` unconditionally draws a `border-b`. The dashboard is the worst case: `DashboardOverviewPage` stacks four `mt-4 grid ... gap-4` rows of cards, and the bottom row is four structurally identical cards (`OutstandingCard`, `RecallsCard`, `FailedRemindersCard`, `OpenClaimsCard` in `AttentionCards.tsx`) that share the same header component, the same `.slice(0, 5)` row list, the same name-left/value-right row, and the same tiny-icon empty state. Nothing on the screen is more important than anything else, so the eye has no entry point. That is the single most recognizable signature of generated UI.

### 1.3 Symptom: the KPI stat card

`StatCard` is the canonical template component: label, big number, hint line, and a pastel-tinted rounded square holding an icon, top-right, in one of four tones.

```44:51:apps/web/src/components/StatCard.tsx
        <span
          className={cn(
            "flex size-10 shrink-0 items-center justify-center rounded-xl",
            toneClasses[tone],
          )}
        >
          <Icon className="size-5" />
        </span>
```

`DashboardKpiRow` then renders exactly four of them in `lg:grid-cols-4` with tones `brand` / `warning` / `success` / `info`. Four evenly-weighted pastel-chip KPI cards in a row is the image that comes out of every "build me a dashboard" prompt. It is also the wrong information architecture here: "Today", "Waiting", "Completed", "Revenue" are not four peers. A front desk at 9am cares about the queue and the next hour; revenue-this-month is a reporting number that does not belong in the same visual tier.

### 1.4 Symptom: literal-metaphor stock icons

109 distinct Lucide icons are in use, all at default stroke weight, and several are the exact choices an LLM makes when it needs to signify a concept rather than communicate one:

| Icon             | Used for                                                                                | Why it reads as generated                                                                                                                            |
| ---------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Stethoscope`    | The product logo, in `AppSidebar.tsx:44,64`, `AuthLayout.tsx:20`, `routes/index.tsx:19` | A stethoscope in a brand-colored rounded square is the default "healthcare app" mark. It is not a logo, it is a placeholder that was never replaced. |
| `Armchair`       | "Waiting room" in the sidebar **and** the mobile bottom tab (`nav-config.ts:37,82`)     | Literal depiction of furniture to mean a queue. Real clinical products show the queue itself or a count.                                             |
| `Bot`            | The AI assistant FAB (`AssistantLauncher.tsx:51`)                                       | Robot-as-AI is the most overused AI signifier there is.                                                                                              |
| `Sparkles`       | AI affordance elsewhere                                                                 | The other most overused one.                                                                                                                         |
| `PhilippinePeso` | Revenue KPI and billing empty state                                                     | Currency glyph as a decorative icon, where the value already renders with a peso sign.                                                               |

No custom icon exists anywhere in the product, including the logo. There is no icon that a designer drew for this app.

### 1.5 Symptom: mandated filler copy

`docs/architecture/design-system.md` §12 codifies a rule: "exactly one `<h1>` per page and **every page carries a description**." `PageHeader` renders that description as muted 14px text under the title. 29 files render `PageHeader`, there are 40 `description` props across the app, and six more descriptions live in the `SectionHub` descriptors. The hub descriptions in `nav-config.ts:180-211` are exactly the kind of sentence that rule forces into existence:

- "Book and manage appointments across your clinic's doctors."
- "Invoices, payments, and insurance coverage."
- "Find a patient, open a chart, or search past visits."
- "Clinic reports and the record of staff activity."

These describe the nav label that is already on screen, already highlighted in the sidebar, one row above. They are the textual equivalent of the pastel icon chip: content that exists to fill a slot.

This also directly contradicts an always-on rule. `.cursor/rules/ui-minimal-copy.mdc` lists under **Do not add unless asked**: "Page or section subtitles under an already-clear title." Two authoritative docs currently disagree, and the one that produces slop is winning because it is the one baked into `SectionHubShell`.

### 1.6 Symptom: thin data, template chrome

The screens carry template scaffolding instead of domain content.

- **Patient list** (`PatientListPage.tsx`) is a 3-column table: Name, Patient #, Contact. No age/sex, no last visit, no next appointment, no outstanding balance, no allergy or flag indicator, no avatar. Every real clinic product puts identity-verification and at-a-glance risk data in this list because that is what the front desk needs to pick the right Juan Santos. Meanwhile the page ships **three view modes** (table / list / grid) including a grid of patient cards, which no front desk will ever use. Chrome was built where data was needed.
- **Waiting room** (`WaitingRoomBoard.tsx`) cards show patient name, scheduled time, doctor, reason. They do **not** show elapsed wait time, which is the one number a waiting room exists to surface. Each card also carries a full-width primary-blue button, so a 9-patient queue renders nine loud blue buttons of equal weight. Empty columns say `Empty`.
- **Every list page** inherits identical `ManagedList` chrome: search + refine + sort + per-page + view switcher + "Showing 1–25 of 120 patients" + pagination. Uniform admin furniture applied regardless of whether a given list needs it.

### 1.7 Symptom: first impressions are unstyled placeholders

The two screens a new user sees first are the two least designed in the product.

```13:34:apps/web/src/routes/index.tsx
    <main className="relative flex min-h-screen items-center justify-center bg-background px-4">
      ...
        <span className="flex size-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
          <Stethoscope className="size-7" />
        </span>
        <h1 className="text-2xl font-semibold text-foreground">DoctorDesk</h1>
        <div className="flex gap-3">
          <Link to="/login" ...>Sign in</Link>
          <Link to="/register" ...>Register</Link>
```

A centered stethoscope glyph, the product name at 24px, and two buttons. `AuthLayout` is the same mark above a `max-w-sm` bordered card. There is no product, no proof, no brand, no craft.

### 1.8 Symptom: motion tuned for a marketing site

`PAGE_TRANSITION` is 300ms translate+fade on every dashboard sub-route (`lib/motion.ts:18`). For an operational tool used hundreds of times a shift, 300ms per navigation reads as sluggish, not polished. Fast, keyboard-driven products keep route changes at or under ~150ms or skip the transition entirely and animate only the content that actually changed.

### 1.9 Symptom: dark mode has no elevation

```267:267:apps/web/src/styles.css
  --card: rgba(255, 255, 255, 0.03);
```

Cards in dark mode are 3% white over the same `#101828` the page and sidebar use. At 3% there is effectively no luminance separation, so every boundary in dark mode is carried by a `#1d2939` border. The result is a flat wireframe look with no surface depth, and it is inherited verbatim from the measured template.

### 1.10 Live-screen observations

A browser pass over the running app at 1440px confirmed the code-level findings and added three that only show up on screen. (The pass was cut short when the local API process died, so a complete screenshot baseline across all routes and breakpoints is a Phase 43 deliverable rather than an input to this plan.)

- **The dashboard shows the same appointment twice, side by side.** `TodayScheduleCard` and `WaitingQueueCard` both rendered "Juan Dela Cruz, 8:00 AM" simultaneously, in adjacent columns, as two differently-shaped representations of one record. Two panels competing to be the same answer is worse than either alone.
- **Spacing rhythm is not actually consistent.** Despite the uniform `gap-4` / `mt-4` values in the source, the perceived gap between the KPI row and the Today section reads tighter than between Today and the chart, because the cards' internal padding differs from the grid gap. Uniform code values do not produce uniform optical rhythm.
- **The app reads airy and marketing-like, not dense and operational.** With one appointment and a 14-day chart occupying two-thirds of the fold, the screen looks like a SaaS demo rather than a tool for someone running a clinic at 9am. This is the opposite of the stated `DESIGN.md` intent ("dense but legible", "clarity over decoration"), which means the tokens and layout are actively fighting the design philosophy the repo already wrote down.
- Minor: the login email placeholder is `clinic@example.com`, generic enough to teach the user nothing.

Also surfaced, and worth a separate bug rather than a design fix: `/dashboard/appointments` rendered "Access denied — your role cannot open this page" for the seeded owner account before resolving to the real list, which suggests permissions are evaluated before the session settles.

### 1.11 What is actually good (do not regress it)

This is not a rewrite-from-zero situation. The engineering substrate is strong and the plan below preserves all of it:

- Real primitive library with `cva` + `data-slot` + `cn()` discipline, no one-off styled divs.
- Enforced pointer contract, `prefers-reduced-motion` paths on every animation, 44px touch targets, `env(safe-area-inset-*)` handling.
- `ResponsiveModal` (sheet below `lg`, dialog above), `BottomTabBar`, `SwipeRevealRow` — the mobile shell exists.
- Per-page skeletons that mirror real markup, plus consistent `EmptyState` / `ErrorState`.
- One place declaring page width (`PageContainer`), one place declaring page gutter (`DashboardShell`), one hub shell owning titles and tabs.
- Rules and skills that agents actually follow.

The problem is the taste layer sitting on top of that substrate, plus a token set that guarantees genericness. That is what this plan replaces.

---

## 2. The anti-slop rule set

This is the deliverable that outlasts the redesign. It becomes `.cursor/rules/anti-slop-design.mdc` (glob-scoped to `apps/web/**/*.tsx` and `styles.css`) plus `.agent/skills/design-review/SKILL.md`.

Every rule below is written as a **pass/fail assertion** that an agent can verify against code or a screenshot. Vibes-level guidance ("make it clean") is deliberately excluded, because that is what produced the current state.

### 2.0 The governing principle

> **Slop is the absence of decisions.**

A generated UI is not ugly because it is badly drawn. It is generic because at every fork the default was taken: default color, default radius, default icon, default layout, default grid, default sentence. Each default is individually defensible, which is why review never catches them. Together they produce a screen that could belong to any product.

Therefore the test for every visual element is: **can someone name the decision behind it, and why the alternative was rejected?** If not, it is slop, regardless of how tidy it looks.

The corollary matters as much as the principle, and it is the trap this plan is most likely to fall into: **you cannot fix slop by adopting a different look.** The 2024 tell was a purple-to-blue gradient on a dark hero. The 2026 tell is a warm cream background, a serif display face, and a sage-green accent, which is what the current generation of design-assistant defaults produces (§3.1). A rule set that bans indigo produces a product that reads as AI in a different colour. So: no look in this plan is adopted because a source recommended it, including the sources cited in §3. They supply checkable rules and evidence, not a palette.

### 2.1 Token rules (T)

| #   | Rule (pass = true)                                                                                                                                                                                                                                                                                                                                                                |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T1  | No color value in the codebase is traceable to a public template, Tailwind's default palette, or shadcn's default theme.                                                                                                                                                                                                                                                          |
| T2  | The brand ramp is authored in OKLCH as **three curves**: a monotonic lightness curve, a hump-shaped chroma curve peaking around steps 400–600 and tapering at both ends, and a near-constant hue. Flat chroma across a ramp is the classic failure, because the 50 and 950 steps clip out of gamut and snap. Gamut-map by chroma reduction (CSS Color 4), never channel clipping. |
| T3  | The primary brand color appears in at most two roles per screen. If three or more distinct element types are brand-colored on one screen, it fails.                                                                                                                                                                                                                               |
| T4  | Neutrals are derived from the brand hue at ultra-low chroma (roughly 0.004–0.012 in OKLCH), so greys carry brand temperature. Pure-neutral gray is a template default.                                                                                                                                                                                                            |
| T5  | A surface elevation scale exists with a measurable luminance step between every adjacent level, in both themes.                                                                                                                                                                                                                                                                   |
| T6  | No dark-mode surface is defined as low-opacity white over the page color (`rgba(255,255,255,0.03)` and similar). Surfaces are **opaque tokens per elevation level**, and raised/overlay levels are always paired with their matching shadow token, since shadows are hard to see in dark mode.                                                                                    |
| T7  | The type scale is explicitly authored: every step declares size, line-height, weight, and letter-spacing.                                                                                                                                                                                                                                                                         |
| T8  | Large text (≥24px) carries negative letter-spacing; small uppercase labels carry positive letter-spacing.                                                                                                                                                                                                                                                                         |
| T9  | Every number that aligns in a column, changes over time, or represents money declares `font-variant-numeric: lining-nums tabular-nums` — **both**, not `tabular-nums` alone. Add `slashed-zero` on financial surfaces.                                                                                                                                                            |
| T10 | The shadow scale has one consistent light direction and is tinted with the app's own neutral hue.                                                                                                                                                                                                                                                                                 |
| T11 | No hardcoded hex or `rgb()` outside the central stylesheet.                                                                                                                                                                                                                                                                                                                       |
| T12 | Nested radii are optically corrected: an inner radius never equals its parent's radius when padding separates them.                                                                                                                                                                                                                                                               |
| T13 | Every token pair used as foreground-on-background passes WCAG 2.2 AA in both themes. AA is the floor, since healthcare procurement and Section 508 reference it. APCA may judge perceptual contrast on top of that, never instead of it.                                                                                                                                          |
| T14 | The neutral ramp is one temperature. Warm-gray and cool-gray tokens never coexist.                                                                                                                                                                                                                                                                                                |
| T15 | Borders, shadows, and muted text are tinted toward the hue of the surface they sit on, not left neutral by default.                                                                                                                                                                                                                                                               |
| T16 | No font weight below 400 appears anywhere in the product.                                                                                                                                                                                                                                                                                                                         |
| T17 | At most three text colors and two weights carry hierarchy on any one screen.                                                                                                                                                                                                                                                                                                      |
| T18 | No grey text on a colored background. De-emphasis on a colored surface uses a hand-picked color at that surface's hue.                                                                                                                                                                                                                                                            |
| T19 | No gradient text (`bg-clip-text text-transparent`), no colored glow (`shadow-[0_0_*]`, saturated `text-shadow`), and no colored 3–4px accent stripe on a card edge.                                                                                                                                                                                                               |
| T20 | Shadows are offset vertically to imply one overhead light source, pairing a soft ambient shadow with a tighter contact shadow.                                                                                                                                                                                                                                                    |
| T21 | The 3:1 contrast allowance is used only for text at or above 24px regular / 18.66px bold. Nothing at 18px claims it.                                                                                                                                                                                                                                                              |
| T22 | Tabular numerals are **not** applied to running prose. Proportional figures read better there, so `tabular-nums` is scoped, never global.                                                                                                                                                                                                                                         |
| T23 | The type ratio is at or below 1.25 (Minor Third 1.2 for dense surfaces), with the small end hand-tuned rather than derived: 14px is the practical minimum for text a user must read on desktop, 13px is for timestamps and metadata only, and form inputs are never below 16px.                                                                                                   |
| T24 | The theme is defined by a **small number of source variables** that generate everything else, not a long hand-maintained list. Linear reduced theirs from 98 variables to three (base color, accent color, contrast).                                                                                                                                                             |
| T25 | `font-optical-sizing: auto` is in effect wherever the face exposes an `opsz` axis.                                                                                                                                                                                                                                                                                                |
| T26 | Layering comes from documented z-index tokens with real values (base 0, sticky 100, dropdown 1000, sticky header 1050, overlay 1100, modal 1200, popover 1300, toast 1400, tooltip 1500). An ad-hoc `9999` is a tell.                                                                                                                                                             |

### 2.2 Layout and hierarchy rules (H)

| #   | Rule (pass = true)                                                                                                                                                                                                                                                                    |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| H1  | Every screen has exactly one dominant element, identifiable in a 3-second squint test.                                                                                                                                                                                                |
| H2  | No screen renders three or more containers of identical visual weight unless they are a genuine repeating set of peers.                                                                                                                                                               |
| H3  | Chrome (border, shadow, background) is opt-in. A container gets it only when grouping cannot be communicated by typography and whitespace.                                                                                                                                            |
| H4  | Spacing encodes relationship: the gap within a group is smaller than the gap between groups, which is smaller than the gap between sections. A single uniform gap value across a screen fails.                                                                                        |
| H5  | Hierarchy is carried by size, weight, and position before color. A screen where removing all color destroys the hierarchy fails.                                                                                                                                                      |
| H6  | Section titles are not wrapped in bordered boxes.                                                                                                                                                                                                                                     |
| H7  | No divider directly under a title that is already separated by whitespace.                                                                                                                                                                                                            |
| H8  | Dense data surfaces (tables, calendar, queue) use compact density; decision surfaces (forms, confirms) use comfortable. Mixing them arbitrarily fails.                                                                                                                                |
| H9  | List/table chrome scales with content. A list that fits on one screen does not render pagination, per-page selectors, and a result count.                                                                                                                                             |
| H10 | No view mode, filter, or toolbar control exists without a named user who needs it.                                                                                                                                                                                                    |
| H11 | Alignment: elements on a screen share a small number of vertical edges. Every new left edge must be intentional.                                                                                                                                                                      |
| H12 | Containers follow the escalation ladder and stop at the first level that works: spacing/gap → divider → section with no border → card. The card is the last resort, never the default page-structure unit.                                                                            |
| H13 | No card is nested inside a card, and a stack of full-width cards is never used as page structure.                                                                                                                                                                                     |
| H14 | A list of records (patients, appointments, invoices, queue entries) renders as rows in a table or list, edge to edge with dividers, never as a grid of cards.                                                                                                                         |
| H15 | Density is a mode with explicit row heights (roughly 32 / 40 / 48px), chosen per surface and per breakpoint, not one global value.                                                                                                                                                    |
| H16 | Exactly one wrapper owns each scroll axis. The page body never scrolls horizontally. Sticky headers are scoped to their scroll wrapper rather than `position: fixed`.                                                                                                                 |
| H17 | Every truncating text node has `min-width: 0` on each flex ancestor between it and its container.                                                                                                                                                                                     |
| H18 | Patient names, patient numbers, error messages, page titles, and button labels are never truncated. Any other truncation has a focus-reachable (not hover-only) way to read the full value.                                                                                           |
| H19 | Sticky and frozen table columns use a **solid** theme-token background that also covers the hover and selected-row states, with an inset box-shadow divider rather than a CSS border. An alpha background lets scrolling content bleed through.                                       |
| H20 | Where content is progressively disclosed in a clinical context, the collapse is visible and states what kind of information is hidden. Silent hiding fails.                                                                                                                           |
| H21 | One layout primitive is repeated enough to become the product's signature, rather than several competing container treatments per screen.                                                                                                                                             |
| H22 | A region shows at most **five visible primary actions** before the rest go to overflow. More than **seven controls** in one region is the trigger to introduce progressive disclosure.                                                                                                |
| H23 | Landmark regions are not conflated: Header, Content, Pane (beside content, content-height), Sidebar (full-height nav), Footer. A header or footer is never rebuilt inside the body where it scrolls away.                                                                             |
| H24 | Line clamping declares all the required properties together and the clamped element carries **no padding**, since the clamp calculation ignores padding and text bleeds.                                                                                                              |
| H25 | `Badge` is used only for counts and enumerated states, never as decoration. Status uses a status indicator.                                                                                                                                                                           |
| H26 | Tables implement the ARIA grid keyboard contract: roving tabindex (exactly one cell at `tabindex="0"`), arrow keys boundary-clamped, Home/End within the row, Ctrl+Home/End to grid extremes, PageUp/PageDown about five rows.                                                        |
| H27 | Destructive confirms default keyboard focus to the **safe** action, use `role="alertdialog"` with `aria-modal="true"` and `aria-describedby` on the warning, and for high-consequence deletes require typing the record's name. A destructive confirm is never placed inside a toast. |
| H28 | Toasts last around 5000ms, pause on hover and focus, and dismiss on roughly a 50px swipe.                                                                                                                                                                                             |

### 2.3 The banned-pattern list (B)

These are the specific visual signatures of generated UI. Each is a hard fail.

One sourcing note, recorded so nobody later mistakes inference for evidence: **B3 (literal-object metaphors) has no published source behind it.** The research pass found named sources banning sparkles, robots, rockets, lightning bolts and lightbulbs as AI signifiers (which covers B4), but nothing written specifically about a stethoscope standing in for "medical" or an armchair for "waiting." B3 is a well-founded extension of the same principle to this product's own icons, and it is the right call, but it is our judgment rather than a citation.

| #   | Banned pattern                                                                                                                                                                                                                                                                                 |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B1  | A KPI/stat card with a pastel-tinted icon chip in a corner.                                                                                                                                                                                                                                    |
| B2  | A row of 3–4 evenly-weighted metric cards at the top of an **operational** screen. (Scope note: a KPI tile row is legitimate as the headline of an **analytical** dashboard, so Insights may have one. Today may not. The failure is using it as the structure of a day-of-operations screen.) |
| B3  | An icon that is a literal picture of a physical object standing in for an abstract concept (armchair = waiting, stethoscope = medical, briefcase = business, rocket = launch).                                                                                                                 |
| B4  | A robot or sparkles glyph to signify AI.                                                                                                                                                                                                                                                       |
| B5  | A currency symbol used as a decorative icon next to a formatted currency value.                                                                                                                                                                                                                |
| B6  | A generic glyph inside a brand-colored rounded square used as a product logo.                                                                                                                                                                                                                  |
| B7  | A page description that restates its title or the nav label that is already on screen.                                                                                                                                                                                                         |
| B8  | A centered `max-w-sm` bordered box as an authentication screen.                                                                                                                                                                                                                                |
| B9  | Gradient fills, glassmorphism, confetti, glow, or animated background effects.                                                                                                                                                                                                                 |
| B10 | A bento-grid arrangement used where the content is not actually of mixed importance.                                                                                                                                                                                                           |
| B11 | Emoji in operational, clinical, or billing UI.                                                                                                                                                                                                                                                 |
| B12 | Every status rendered as the same pastel pill shape, distinguishable only by hue.                                                                                                                                                                                                              |
| B13 | Placeholder text that duplicates the field label.                                                                                                                                                                                                                                              |
| B14 | A `.slice(0, N)` list with no indication that more items exist.                                                                                                                                                                                                                                |
| B15 | An action or row that navigates to a list page instead of the specific record it names.                                                                                                                                                                                                        |
| B16 | A "Learn more", "Read more", "Get started", or "Explore" label anywhere in the authenticated product.                                                                                                                                                                                          |
| B17 | Identical structural markup repeated for items that carry different meaning (four different concerns rendered as four identical cards).                                                                                                                                                        |
| B18 | An icon added purely to fill horizontal space.                                                                                                                                                                                                                                                 |

### 2.4 Icon rules (I)

Icon rules **split by surface**, and getting this wrong in either direction is a real failure mode. Minimalism belongs in nav and chrome. It does not belong on a calendar block, a queue card, or a patient header, where clinical staff need a dense alert vocabulary. A healthcare team that collapsed its calendar alerts into two icons behind a tooltip found staff hunting for information while a patient waited (§3.4). The condition that makes density work there is a **legend**, not fewer icons.

| #   | Rule (pass = true)                                                                                                                                                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| I0a | **Nav and chrome:** icons are minimal and never decorative. No icon where the label alone is unambiguous.                                                                                                                                           |
| I0b | **Clinical surfaces (calendar block, queue card, patient header, chart):** a dense alert vocabulary is allowed and encouraged, on the condition that every icon maps to exactly one documented meaning and a legend is reachable from that surface. |
| I1  | One icon set, one stroke weight per context, with stroke/size/color explicitly set rather than left at Lucide's defaults (2px at 24px in `text-muted-foreground`).                                                                                  |
| I2  | Icon size is derived from the cap-height of adjacent text, not chosen per site.                                                                                                                                                                     |
| I3  | Decorative icons are `aria-hidden`; icon-only controls have an `aria-label`.                                                                                                                                                                        |
| I4  | Icons are optically centered in their container, not mathematically centered.                                                                                                                                                                       |
| I5  | The product mark and any flagship-feature mark are custom SVGs, not set glyphs.                                                                                                                                                                     |
| I6  | An icon communicates a category or action. If the adjacent text already does that unambiguously, the icon is removed.                                                                                                                               |
| I7  | No concept has two different icons across the app, and no icon serves two concepts.                                                                                                                                                                 |
| I8  | Icons beside a text label are lower-contrast than the label, and the icon/text lockup is optically balanced (±1px adjustments allowed).                                                                                                             |
| I9  | No emoji stands in for a UI icon in nav, headings, rows, or list bullets.                                                                                                                                                                           |

### 2.5 Data and domain rules (D)

The strongest signal that a product was designed by someone who understands the domain.

| #   | Rule (pass = true)                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | Every list shows the fields a real user needs to make the decision that list exists for, not the fields that were easiest to query.                                                                                                                                                                                                                                                                                                                                     |
| D2  | Any screen showing a queue or a wait shows elapsed time, live.                                                                                                                                                                                                                                                                                                                                                                                                          |
| D3  | Any screen identifying a person shows enough to disambiguate two people with the same name.                                                                                                                                                                                                                                                                                                                                                                             |
| D4  | Safety-critical data (allergies, alerts, outstanding balance, terminal status) is impossible to miss on the screen where it matters.                                                                                                                                                                                                                                                                                                                                    |
| D5  | Status is encoded on at least two channels (not color alone), so it survives grayscale and color-blindness. Distinct **shapes** per state, plus a text label, plus `aria-label="Status: …"`, with `role="alert"` for urgent and `role="status"` for informational.                                                                                                                                                                                                      |
| D5a | The **categorical palette excludes red entirely**, so an appointment-type color can never be mistaken for a status color. Red is reserved for status. NHS Scotland's design system does exactly this, and DoctorDesk has both palettes on the same calendar.                                                                                                                                                                                                            |
| D5b | Red and green are never the sole differentiator between two clinical statuses.                                                                                                                                                                                                                                                                                                                                                                                          |
| D5c | A status **transition** is signalled by more than a hue swap. In a comparative usability study, nurses "did not initially notice a change in colours," so a change of state gets a deliberate shape change or a brief motion cue. This is one of the few places in this product where motion is justified on safety grounds rather than polish.                                                                                                                         |
| D5d | Each status has a documented threshold definition, and the same term is used for it in the calendar, the table, and the badge.                                                                                                                                                                                                                                                                                                                                          |
| D15 | Any list that can exceed ~50 rows is virtualized. Patient registries and appointment history will.                                                                                                                                                                                                                                                                                                                                                                      |
| D16 | Forms follow the rules that separate a working form from a demo one: the submit button stays enabled until the request actually starts (disabling on invalid hides _why_), a loading button keeps its label rather than becoming a bare spinner, free-text input is accepted and validated afterward rather than rejected on keypress, the first invalid field receives focus on failed submit, navigating away from unsaved changes warns, and paste is never blocked. |
| D6  | Empty, single-item, loading, error, and permission-denied states are designed per surface, not handled by one generic component everywhere.                                                                                                                                                                                                                                                                                                                             |
| D7  | Numbers that represent the same quantity are formatted identically everywhere they appear.                                                                                                                                                                                                                                                                                                                                                                              |
| D8  | A skeleton matches the loaded markup closely enough that no layout shift occurs.                                                                                                                                                                                                                                                                                                                                                                                        |
| D9  | Loading obeys thresholds: nothing under ~1s, a layout-mirroring skeleton from ~1–10s, determinate progress past 10s. A background refresh never re-blanks data that is already on screen.                                                                                                                                                                                                                                                                               |
| D10 | Three distinct empty states exist where they apply and are not collapsed into one: first-run (nothing yet), filtered-to-nothing, and zero-as-a-win (an empty queue is good news).                                                                                                                                                                                                                                                                                       |
| D11 | A load failure states the cause and an action. "An error occurred" fails.                                                                                                                                                                                                                                                                                                                                                                                               |
| D12 | Clinical abbreviations are preferred over expanded prose in dense surfaces, because clinicians read them faster and asked for more of them (§3.4).                                                                                                                                                                                                                                                                                                                      |
| D13 | Dates, times, currency, and numbers are formatted through `Intl.*`, never hand-rolled, and never in an ambiguous form like `01/02/2026`.                                                                                                                                                                                                                                                                                                                                |
| D14 | No dead ends. Every state offers a next step or a recovery path.                                                                                                                                                                                                                                                                                                                                                                                                        |

### 2.6 Copy rules (C)

Extends `human-copy.mdc` and `ui-minimal-copy.mdc`; does not replace them.

| #   | Rule (pass = true)                                                                                                         |
| --- | -------------------------------------------------------------------------------------------------------------------------- |
| C1  | Removing the string would make the screen harder to use. If not, the string is deleted.                                    |
| C2  | No em dash. No "This lets you…", "Simply", "Easily", "Just".                                                               |
| C3  | No adjective that a competitor could not also claim.                                                                       |
| C4  | Error copy names what happened and the next step. Nothing else.                                                            |
| C5  | Button labels are verbs describing the specific outcome, never "Submit", "OK", or "Continue" where a specific verb exists. |
| C6  | Copy uses the vocabulary the clinic uses, not the vocabulary the database uses.                                            |
| C7  | Truncation uses the ellipsis character `…`, never three periods.                                                           |
| C8  | Non-breaking spaces hold together units, names, and figures that must not wrap apart ("Dr. Santos", "2 pm", "₱1,200").     |
| C9  | Patient numbers, record IDs, and drug names carry `translate="no"` so browser translation cannot mangle them.              |

### 2.7 Motion and feel rules (M)

Whether to animate at all is decided by **frequency**, before duration is even discussed (§3.3):

| How often the user triggers it                                             | Decision                             |
| -------------------------------------------------------------------------- | ------------------------------------ |
| 100+ per day (keyboard shortcuts, command palette, list navigation by key) | No animation, ever                   |
| Tens per day (hover, row selection, **route changes in a dashboard**)      | Near-imperceptible, or nothing       |
| Occasional (modals, sheets, toasts, confirms)                              | Standard animation                   |
| Rare or first-run (onboarding, a completed day)                            | The entire delight budget lives here |

Durations, once an animation is justified: press 100–160ms, tooltips and small popovers 125–200ms, dropdowns and selects 150–250ms, modals and sheets 200–500ms. **Hard ceiling of 300ms for any UI animation.**

| #   | Rule (pass = true)                                                                                                                                                                                                                    |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M1  | Route-change animation is at or under 180ms, or absent. The current 300ms translate+fade fails.                                                                                                                                       |
| M1b | No animation fires on a command-palette toggle, a keyboard shortcut, or any other 100+/day action.                                                                                                                                    |
| M1c | No UI animation exceeds 300ms without a written reason.                                                                                                                                                                               |
| M1d | `ease-in` is never used on a UI element, because it delays the first movement, which is the moment the user is watching most closely. No `transition: all`.                                                                           |
| M1e | Only `transform` and `opacity` animate. Never `top`, `left`, `width`, or `height`. Framer Motion's `x`/`y`/`scale` shorthands are not hardware-accelerated, so the full `transform` string is used.                                   |
| M1f | Popovers and menus scale from `var(--transform-origin)`, starting at 0.9–0.97 with opacity, never from `scale(0)`. Modals are exempt and stay centered.                                                                               |
| M1g | Rapidly re-triggered elements use interruptible transitions or springs, never keyframes.                                                                                                                                              |
| M1h | Hover motion is gated behind `@media (hover: hover) and (pointer: fine)`, since touch devices fire hover on tap.                                                                                                                      |
| M2  | Motion explains causality (where something came from, what changed). Motion that only decorates is removed.                                                                                                                           |
| M3  | Elements that enter from a trigger animate from that trigger's position.                                                                                                                                                              |
| M4  | No animation delays input. Press feedback is immediate; the visual can settle after.                                                                                                                                                  |
| M5  | Every animation has a `prefers-reduced-motion` path. Prefer a gentler variant over removing motion entirely, so causality is still communicated.                                                                                      |
| M6  | No affordance is revealed only on hover. Every hover affordance has a touch equivalent.                                                                                                                                               |
| M7  | Touch targets are ≥44×44px on touch and ≥24×24px on desktop, or satisfy the WCAG 2.5.8 Spacing exception. Where the visual target is smaller, the hit area is expanded beyond the visual bounds. `touch-action: manipulation` is set. |
| M8  | Scroll position is restored on back navigation.                                                                                                                                                                                       |
| M9  | Sheets respond to drag with physics, dismiss at a sensible threshold, and avoid the on-screen keyboard via `visualViewport` rather than fixed-position workarounds.                                                                   |
| M10 | Every gesture (swipe, drag, pinch) has a tap and keyboard equivalent.                                                                                                                                                                 |
| M11 | Gestures trigger on release, not on threshold cross, and content occluded by the finger is accounted for.                                                                                                                             |
| M12 | URL reflects filters, tabs, pagination, and expanded panels. Navigation uses anchors so Cmd/Ctrl/middle-click work.                                                                                                                   |
| M13 | `overscroll-behavior: contain` on modals and sheets. Text selection is disabled during drag.                                                                                                                                          |
| M14 | View Transitions are progressive enhancement only (Firefox stable lacks cross-document support), and `navigator.vibrate` is never load-bearing (no iOS Safari support).                                                               |

### 2.8 The review procedure

The `design-review` skill runs this loop, and a human should run the same one. The structure borrows from two published design-review agents (§3.7), because their hard-won constraints are what stop a review from degenerating into adjectives.

**Operating posture.** Default to flagging. Approval is earned, not assumed. A reviewer that finds nothing has not reviewed.

**Order matters.** The rubric loads before the critique starts, so grading is consistent between runs. Version the rubric alongside the skill, or fetch it, so it cannot silently go stale relative to the rules file (Vercel's own design-guidelines skill fetches its guidelines fresh before every review for exactly this reason).

**The blunt test, applied first.** _If someone told you an AI made this screen, would you believe them immediately?_ If yes, say so in the first line of the report and name the three elements responsible. Everything after that is detail.

1. **Capture.** Screenshot the surface at 375 / 820 / 1440px in both themes. Never review from code alone, because slop is a visual property. Never review from screenshots alone either, because the fix lives in code.
2. **Deterministic sweep first.** Run `check:design-slop` (computed-style and AST checks). Anything a script can decide is not left to judgment. This mirrors the method behind the only quantitative slop audit found (§3.2), which deliberately avoided LLM screenshot-judging because it reintroduces the bias being measured.
3. **Squint test (H1, H5).** Blur the screenshot: is there one clear entry point? Convert to grayscale: does the hierarchy survive?
4. **Template test.** Which template does this look like? If the answer is specific, name the elements that caused it.
5. **Decision audit (§2.0).** Take the five most visually prominent choices on screen. State the decision and the rejected alternative for each. Any that cannot be answered is slop.
6. **Rule sweep.** Walk T, H, B, I, D, C, M. Record each violation with `file:line`.
7. **Domain test (D1).** Ask a front-desk-at-9am question of the screen: _who has waited longest? which Juan Santos is this? what do I do next?_ If the screen cannot answer it, visual work is premature and the finding is a data problem, not a design problem.
8. **Report.**

**Report format, and these constraints are the point:**

- **At most six issues, ranked by visual impact.** No minimum, no padding. Two issues gets two, plus one line saying why the list is short.
- **Before / After / Why** per issue.
  - _Before is a fact, never a feeling._ "Four containers at identical weight in a 4-column grid, each with a 40px tinted icon chip" passes. "This feels cluttered" does not.
  - _After_ must fit inside an hour of work. A rewrite is not an After; it is a separate finding.
  - _Why_ is exactly one citation: a rule ID from §2, a WCAG success criterion, or a named source from §3. Never an uncited opinion.
- **Statuses, not scores.** Each swept rule is `pass` / `fail` / `partial` / `not applicable` / `cannot tell from this artifact`. No percentage and no aggregate score, so "not applicable here" never looks like failure.
- **A durable-fix column.** For each issue, name the lint rule, token, primitive, or test that stops that _family_ of failure from coming back. A review that only fixes instances guarantees a re-review.
- **Close by naming the one fix that matters most.**
- **Never an empty pass.** A screen with no violations still gets two or three polish items.
- **Banned words in the report itself:** _effectively, leverages, seamless, streamlined, optimises, robust, elevate._ A review written in that register cannot be trusted to detect the same register in the product.

**Remedial preference order.** When proposing a fix, work down this list and stop at the first option that resolves it. The ordering matters because the cheapest and most common correct answer is the one agents reach for last.

1. **Delete it.** Most slop is additive. Removing the element beats styling it.
2. Reduce it (fewer, smaller, quieter).
3. Change the token, not the component.
4. Change the component, not the screen.
5. Restructure the screen.
6. Rebuild.

**Ship criteria.** A screen ships when it has zero B-class violations and no unresolved H-class violations. When a screen sits between two verdicts, **the cost of the fix decides** (rebuild / restructure / craft pass / a few discrete fixes / nothing material). A violation count is evidence, not a threshold: five small issues on a sound structure are better than one issue that blocks the task.

**One instruction for whoever directs this work, human or agent.** Do not review or request changes in adjectives. "Cleaner," "more premium," "less generic," and "make it pop" fuse taste direction with implementation and leave nothing to anchor on, which is precisely the condition that produces averaged-out defaults. State the rule, the surface, and the intended outcome instead.

---

## 3. Reference research

A research pass covered AI-slop tells, published craft rubrics, healthcare product patterns, and design-review agent structures. Sources are tagged by reliability, because a large share of what currently ranks for "AI slop design" is itself AI-generated SEO content. Only material worth acting on is recorded here.

### 3.1 The one finding that reframes everything

Every credible source converges on the same principle, independently:

> **A tell is an unspecified default, not a banned value.**

This matters because the obvious response to "our app looks AI-generated" is to adopt a different look, and that fails. The [Unslop UI](https://www.claudecodehq.com/playbooks/unslop-ui) catalogue makes the point sharply: the 2024 tell was a purple-to-blue gradient on a dark hero; the **2026 tell is a warm cream background with a serif display face (Instrument Serif, Fraunces) and a sage or forest-green accent**, and it names Claude's own frontend-design skill as the thing producing it. Swapping the first for the second is not unslopping, it just resets the clock.

Practical consequence for this plan: **do not adopt a look from a list of recommended looks.** §2.0's "can you name the decision" test is the right primitive, and it happens to be what Vercel, Emil Kowalski, Linear, and the one quantitative audit all reduce to.

### 3.2 The quantitative audit, and its method

Adrian Krebs scored 1,590 Show HN landing pages for 16 slop patterns, reported via [Developers Digest](https://www.developersdigest.tech/blog/ai-design-slop-and-how-to-spot-it). Results: **22% heavy slop** (4+ patterns), 32% mild, 46% clean. Most common single tell was a permanent dark theme (34%), then gradient backgrounds (27%), then **icon-card grids (22%)**.

The method is the part to steal: Playwright loads each page headless, an in-page script walks the DOM reading **computed styles**, and every pattern is a deterministic CSS/DOM check. No LLM judging screenshots, because that reintroduces the bias being measured. ~5–10% false positives on manual QA.

**That is exactly the design of the `check:design-slop` script and screenshot harness in Workstream G.** Deterministic checks on computed styles, LLM review only for the judgment calls a checker cannot make.

Patterns from the 16 that apply to this codebase: identical feature cards with an icon on top; stat banner rows; colored accent stripes on cards (a designer quoted in the piece: _"colored left borders are almost as reliable a sign of AI-generated design as em-dashes for text"_); all-caps section labels; shadcn defaults; glassmorphism.

What the clean 46% did, and the single highest-leverage discipline named: **one strong layout primitive repeated until it becomes the product's signature**, rather than seven card treatments and three stat banners.

The shadcn fingerprint is identifiable from a screenshot in under three seconds, per [Sailop](https://sailop.com/blog/shadcn-ui-design-monoculture-2026): `rounded-lg border bg-card shadow-sm` repeated, `baseColor: slate` untouched, Lucide at 2px/24px in `text-muted-foreground`, and a `grid md:grid-cols-3 gap-8` of three identical cards. DoctorDesk matches on the card recipe, the Lucide defaults, and the icon-card grid.

### 3.3 Craft rubrics worth borrowing

| Source                                                                                                                                                                                                                     | What to take                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Vercel Web Interface Guidelines](https://vercel.com/design/guidelines) ([raw AGENTS.md](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/AGENTS.md))                                           | The best directly-usable rubric found. Written as MUST/SHOULD/NEVER, which is why §2 is written the same way. Highest-value rules for this app: `tabular-nums` for compared numbers; skeletons mirror final content; redundant (non-color-only) status cues; no dead ends; `min-w-0` on flex ancestors of truncating text; URL reflects filters/tabs/pagination; Back/Forward restores scroll; nav uses anchors so Cmd-click works; animate only `transform`/`opacity`, never `transition: all`; nested radii concentric and child ≤ parent; tint borders and shadows toward the background hue; layered shadows (ambient + direct); mobile `<input>` ≥16px to stop iOS zoom; expand hit area when the visual target is under 24px.                                            |
| [Emil Kowalski, Good vs Great Animations](https://emilkowal.ski/ui/good-vs-great-animations) + his [review-animations skill](https://raw.githubusercontent.com/emilkowalski/skills/main/skills/review-animations/SKILL.md) | A **frequency table** that decides whether to animate at all: 100+/day (shortcuts, command palette) → never animate; tens/day (hover, list nav) → near-imperceptible or nothing; occasional (modals, drawers, toasts) → standard; rare/first-run → the delight budget. Durations: press 100–160ms, tooltips 125–200ms, dropdowns 150–250ms, modals/drawers 200–500ms, and a hard ceiling of 300ms for UI animation. `ease-in` on UI is a block. Press feedback `scale(0.97)`. Stagger 30–80ms. Popovers scale from `var(--transform-origin)`, never `scale(0)` (start 0.9–0.97 + opacity); modals exempt and stay centered. Gate hover motion behind `@media (hover: hover) and (pointer: fine)`. Framer Motion's `x`/`y`/`scale` shorthands are **not** hardware-accelerated. |
| [Refactoring UI](https://medium.com/refactoring-ui/7-practical-tips-for-cheating-at-design-40c736799886)                                                                                                                   | Never a font weight below 400 in UI. At most 3 text colors and 2 weights; don't let size carry hierarchy alone. **Never grey text on a colored background** (hand-pick a color at the background's hue instead). **Emphasize by de-emphasizing** when nothing can be added. Offset shadows vertically rather than raising blur. A five-level shadow scale combining one soft ambient shadow with one tighter contact shadow. Rotate hue toward cyan/magenta/yellow to add perceived brightness rather than only raising lightness. The 3:1 contrast allowance applies only at ≥24px regular or ≥18.66px bold.                                                                                                                                                                  |
| [Rauno Freiberg, Invisible Details of Interaction Design](https://rauno.me/craft/interaction-design) + [Designing Depth](https://rauno.me/craft/depth)                                                                     | Explicitly not a checklist. Principles: reuse metaphors so interaction rewards learning; design for the finger occluding what it touches; gesture thresholds trigger on release, not on cross; dim/blur the backdrop to simulate depth of field; **delay a reveal deliberately** when two layers share space, since a simultaneous linear reveal reads as a layering error; a surface that stays interactive should behave differently from one that recedes.                                                                                                                                                                                                                                                                                                                  |
| [WCAG 2.2 SC 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)                                                                                                                                  | 24×24px at AA with five exceptions, and the one that matters is **Spacing**: center a 24px circle on each undersized target's box; if no circles intersect, it conforms. Restyling a native control with CSS removes the User Agent Control exception. 44×44 is AAA (2.5.5) and matches Apple's 44pt.                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| [Material 3 Expressive research](https://design.google/library/expressive-material-design-google-research)                                                                                                                 | 46 studies, 18,000+ participants; eye-tracking found key elements spotted **up to 4× faster**, with the gap between older and younger users narrowing. The transferable findings here are the **non-motion** ones: larger targets, higher-contrast containment, and exceeding minimum tap-target and contrast standards improved speed for all ages and abilities. Its spring-overshoot motion system is the wrong bet for a clinical tool (see §3.6).                                                                                                                                                                                                                                                                                                                         |

### 3.4 Healthcare product patterns

Verified detail was only available for a handful of products; the rest are behind logins and returned only marketing pages. What was found is unusually on-point.

**[Athelas Air calendar redesign](https://www.alexyoungdavies.com/projects/athelas-air-calendar) — the most directly relevant document found.** A healthcare team shipped exactly the shadcn-default treatment and measured the result:

> "Our extra padding, bigger font sizes, and backgrounds on icons were requiring bigger footprints on the UI. This was likely the cause of staff feeling **'too zoomed in'** and wanting **'a better birds eye view'** of the day ahead."

That is this plan's complaint, diagnosed and fixed by someone who measured it. Their teardown of competing clinical calendars: 5+ providers visible at once; alerting deliberately "vast and detailed" (title icons, colored dots) with **a legend to decode it**; appointment type by color and alerts by block style; unavailable time as solid untitled grey; appointment blocks never exceeding 50% of column width; **a pop-out for appointment detail rather than navigating away**. Their post-launch learning: the pop-out was missing email, phone, and next scheduled visit, which staff needed while the patient waited.

**[Jane App schedule](https://jane.app/guide/lesson-1-schedule).** Day / Week / Staff Today views, week default for a single practitioner. Practitioners listed left, `+` to compose a multi-practitioner view, custom views savable. A neat inversion worth copying: **shifts carry a light blue background and white means unavailable**, so bookable time is the figure and unavailable time is the ground. Number keys **1–7 set how many upcoming days are shown**, which their docs call a staff favourite: a cheap, high-value density control.

**[Epic Cadence](https://epicsupport.sites.uiowa.edu/epic-resources/scheduling).** Four transferable patterns: an **Appointment Desk** that is a patient-centric hub _distinct from the calendar_ (demographics, guarantor, insurance, appointment history, future appointments, schedulable orders, with filterable tabs); a **persistent patient context rail** (Storyboard); **right-click as a first-class action surface** on the schedule grid; and the same provider schedule reachable both inside and outside a booking task.

**EHR density research** ([MICU clinician display-preference survey](https://doi.org/10.4338/aci-2017-04-ra-0060), [UNC screen-transition study](https://cdr.lib.unc.edu/downloads/fj236b318?locale=en)). Clinicians actively want density: only 15% preferred verbose text descriptors, 57% preferred abbreviated text, 60% preferred colour-coding, and **63% wanted more clinical abbreviations** specifically to raise information density. 64% would accept the system hiding low-yield data, but 56% require an indicator of _what type_ was hidden and 23% would not trust hiding rules at all, so **progressive disclosure in a clinical UI must be visible disclosure**. The named failure mode is _information sprawl_: "the EHR made it harder to build the patient's story." The four most-visited screens were all high-density with minimal dead space and high navigational flexibility.

**Ambient AI scribes.** Only product-philosophy level detail was available, from low-reliability sources. The one transferable idea, from Nabla: make the model's **in-progress reasoning visible and interruptible** rather than showing a spinner followed by a finished block. That fits the existing Tier-2 draft-then-confirm model rather than replacing it.

**On card soup specifically:** no evidence was found of any clinical scheduling product using a KPI-card grid as its day-of-operations screen. Jane and Epic's scheduling surfaces are grid/table/panel based.

### 3.5 Card soup, stated well

[Alex Chernysh, Interface Design for Serious Products](https://alexchernysh.com/blog/interface-design-serious-products):

> "The fastest route to a cheap-looking modern product is card soup. When every block is tinted, rounded, shadowed, and framed as if it were equally important, the page stops communicating hierarchy and starts looking like a component library demo."

And the corrective: "Structured content often wants lists for scan speed, tables for comparison, rows for operational status, one framed panel for the thing that needs containment. Cards earn their place when content has internal structure or a hoverable object needs a visible boundary. They should not be the default answer to every layout question."

Also from the same source, a diagnosis that applies to the 300ms page transition: _"Bad motion is usually compensating for weak hierarchy. It adds energy where the design should have added clarity."_

The **container decision ladder** (weakest to strongest) is the operational form of this, and becomes rule H3a in §2: spacing/gap → divider → section (no border) → card, with the card as the last resort rather than the default.

On **bento grids**: avoid for this product. The technical objection is that bento requires filling all available space, so removing one block breaks the composition and it cannot reflow across arbitrary viewports without stretch rules that damage the content. It also risks a WCAG 1.3.2 Meaningful Sequence failure when visual order diverges from DOM order. Sources disagree on whether bento reads as AI, but they agree it is wrong for a data-dense operational dashboard.

Density targets for an expert daily-driver tool: side nav 240–280px (DoctorDesk is at 256px, fine), inspector panels 340–420px, and **row heights of 32 / 40 / 48px by density mode** rather than one value.

### 3.6 Where sources disagree, and how this plan resolves it

These are the calls that needed making rather than averaging.

| Conflict                                                                                                                                                                                                                                                                                                                                                        | Resolution for DoctorDesk                                                                                                                                                                                                                                                                                                   |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Anti-slop advice generates the next slop.** Some sources recommend exactly the cream/serif/sage look another source flags as the current top tell.                                                                                                                                                                                                            | Neither. §2.0's decision test governs; no look is adopted from a list of looks.                                                                                                                                                                                                                                             |
| **APCA vs WCAG.** Vercel says "prefer APCA over WCAG 2."                                                                                                                                                                                                                                                                                                        | WCAG 2.2 AA is the floor, non-negotiable: it is what Section 508, regulators, and healthcare procurement reference. APCA is a useful _design_ tool for judging perceptual contrast. Meet WCAG, optimise with APCA, never substitute.                                                                                        |
| **Density vs touch targets.** Linear-style density (13px body, 32–36px rows) collides with 24px (AA) and 44px (this repo's own rule).                                                                                                                                                                                                                           | Density becomes a **mode**, not a global. Desktop uses compact rows and leans on the WCAG 2.5.8 **Spacing** exception deliberately, plus hit areas expanded beyond visual bounds. Mobile keeps comfortable rows and the 44px rule unchanged. This resolves a tension the current plan would otherwise hit in Workstream B3. |
| **Icon minimalism has a floor in clinical UI.** Linear's refresh cut icon usage and removed coloured icon backgrounds; Athelas found that collapsing alerts into two icons with a tooltip made staff _hunt_ for information while a patient waited, and that competitors' "visually cluttered" multi-icon approach served users better because it had a legend. | **Split the rule by surface.** Apply icon minimalism to nav and chrome. Do **not** apply it to calendar blocks, queue cards, or the patient header, where a dense multi-icon alert vocabulary plus a legend is correct. This directly revises Workstream C.                                                                 |
| **"Don't use Inter" is overstated.** It is simultaneously the #1 tell and a font engineered for small-size screen legibility, shipped by Linear.                                                                                                                                                                                                                | Confirms decision #2 in §8: keep IBM Plex Sans. The rule is whether a choice was made and whether the scale is tuned, not which face.                                                                                                                                                                                       |
| **Dark-mode elevation.** Material 2's white-overlay system is the origin of "white at 3%"; Material 3 deprecated it. Atlassian pairs lighter opaque surfaces with shadows; M3 says use shadows sparingly; Linear uses LCH lightness steps.                                                                                                                      | All sources agree on the two negatives: do not stack alpha overlays, and do not rely on shadow alone in dark mode. Confirms T6 and A3.                                                                                                                                                                                      |
| **Motion: crisp vs expressive.** Emil's rubric caps UI motion at 300ms and says a dashboard "stays crisp." M3 Expressive's spatial springs deliberately overshoot and bounce, with 4× faster element-spotting reported.                                                                                                                                         | Emil's rubric wins for a tool used under time pressure. Take M3 Expressive's non-motion findings (targets, contrast, containment) and leave its spring overshoot alone.                                                                                                                                                     |
| **Progressive disclosure vs clinician trust.** General product advice says hide advanced controls; the MICU survey found 23% of clinicians would not trust hiding rules.                                                                                                                                                                                        | In any chart or clinical context, hiding must be **visible and labelled**: show that something is collapsed and what kind of thing it is.                                                                                                                                                                                   |
| **Cards.** Material 3 treats the card as a core container; the dense-product-UI sources treat it as a last resort.                                                                                                                                                                                                                                              | Not a real conflict: M3 is mobile-first, and the dense sources are reacting to the card being used as the default page-structure unit, which is precisely this codebase's problem. Ladder in §3.5 applies.                                                                                                                  |
| **Em dash ban.** This repo's `human-copy.mdc` bans it with zero tolerance.                                                                                                                                                                                                                                                                                      | Keep the house rule, but record that it is a deliberate overcorrection adopted because of the AI-tell association, not a typographic standard. Nobody should "fix" it later thinking it was a mistake.                                                                                                                      |
| **Glassmorphism.** One source calls it a core AI fingerprint; another measures it at 0.2% and "contested."                                                                                                                                                                                                                                                      | Moot: already banned by `motion.mdc` and B9.                                                                                                                                                                                                                                                                                |

### 3.7 Published design-review agents

Two are worth copying structurally for the `design-review` skill in Workstream G.

**[humbleteam/design-review](https://github.com/humbleteam/design-review)** — the best-structured one found:

- **Rubric loads before the critique**, so scoring is consistent run to run.
- Issue list **capped at 6, ranked by impact**, with no minimum and no padding. Two issues gets two, plus one line explaining why the list is short.
- **Before / After / Why** per issue. _Before is a fact, never a feeling_: "12 elements inside a 320px card with no grouping," not "this feels cluttered." _After_ must fit inside an hour. _Why_ is exactly one citation (a Nielsen heuristic, a WCAG success criterion, or a named platform guideline), never an uncited opinion.
- Tie-break when a screen fits two bands: **the cost of the fix decides** (rebuild / restructure / craft pass / a few discrete fixes / nothing material). A count of violations is evidence, not a threshold, so five small issues on a sound structure score better than one issue that blocks the task.
- Close by naming **the one fix that matters most**. Even a top score gets 2–3 polish items; never an empty pass.

**[Checklist-Design/skills](https://github.com/Checklist-Design/skills)** — two modes. `audit` walks a checklist as a table with five statuses (present / partially present / missing / not needed / can't tell) and deliberately **no score or percentage**, because "not needed here" should not look like failure. `critique` is peer-review prose with an explicit **blocklist of AI-report words** (_effectively, leverages, optimises, streamlined_).

Four more, for the ideas worth lifting:

- **[EnchStyle/ui-ux-audit-skill](https://github.com/EnchStyle/ui-ux-audit-skill)** — 15 categories including "generic-AI aesthetic and copy quality," a score with the arithmetic shown and explicit severity weights (Blocker −12, Critical −8, Warning −4, Polish −1), and the distinctive part: **durable-fix recommendations**, naming the lint rule or automated test that stops each failure family from returning. That column is now in §2.8.
- **[Emil Kowalski's review-animations](https://raw.githubusercontent.com/emilkowalski/skills/main/skills/review-animations/SKILL.md)** — contributes the **operating posture** ("default to flagging; approval is earned, not assumed"), a **remedial preference hierarchy** that starts with _delete_, and an explicit Block/Approve verdict with named block conditions. All three are in §2.8.
- **[rodrgds/openpost critique skill](https://github.com/rodrgds/openpost/blob/main/.agents/skills/critique/SKILL.md)** — has an "AI Slop Detection (CRITICAL)" section whose entire test is _"If someone said 'AI made this,' would you believe them immediately?"_ Adopted as the first step of the report.
- **[Vercel's web-design-guidelines skill](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md)** — trivially simple, and worth copying for one reason: it **fetches the guidelines fresh from a URL before every review** rather than embedding them, so the rubric cannot go stale. Ours is local, so the equivalent is versioning the rubric against the rule file.

### 3.8 Dense-surface specifics worth keeping

A catalogue of product-UI rules (the `product-ui-taste` skill, plus [Astryx's layout docs](https://astryx.atmeta.com/docs/layout)) supplied most of the concrete numbers now embedded in §2.1–2.2. The framing that made them usable: read the surface type, set three dials (density, data complexity, consequence), **budget the frame in pixels before filling it**, then fill.

Its container policy by archetype is the sharpest statement of DoctorDesk's problem:

| Archetype                                                            | Container policy                                               |
| -------------------------------------------------------------------- | -------------------------------------------------------------- |
| Tracker / work tool (issues, tickets, **clinic queue and schedule**) | **Rows only. Zero cards.**                                     |
| Console / observability                                              | Card grid for dashboard widgets; table for everything else     |
| Settings / forms                                                     | Form sections; card only to group dangerous or billing actions |

And the line worth pinning above the work:

> "The single fastest way to make a product screen look like an AI prototype is to wrap every record in a Card with a Badge."

That is a literal description of `WaitingRoomCard` and the patients grid view today.

Two closing notes from the research worth recording:

- **Scroll ownership is named the number-one product-UI layout bug**, ahead of anything aesthetic. Hence H16.
- **Naming a strict, well-defined design language collapses an agent's option space.** The mechanism behind generated-looking output is not bad taste, it is too many equally-valid options and no constraint, so the model averages. A specified design language is therefore not bureaucracy on top of the design work; it is the thing that makes agent-built UI non-generic. That is the load-bearing argument for Workstream G existing at all.

---

## 4. Workstreams

Eight workstreams, ordered by dependency. A through C are foundational and must land before D, because redesigning 46 pages against the current token set would just re-skin the same template. G runs alongside everything so that each landed screen is graded before the next starts.

### Workstream A — Owned visual identity

The point of this workstream: after it lands, no token in the app can be traced to TailAdmin, Tailwind defaults, or shadcn defaults.

**A1. Revoke the "match TailAdmin exactly" decision**

- [x] Rewrite `docs/architecture/design-system.md` §3.2 and §11.1 to record that the verbatim-adoption decision is revoked, with the reason (it is the cause of the generic read). Keep the historical note — future agents need to know why not to re-apply it.
- [x] Reframe the whole doc as "reference audit of a template we studied," not "our token spec." Its current `**Status: implemented.**` banner makes it read as authoritative.
- [x] Move the authoritative token spec to a new `docs/architecture/design-language.md` that describes DoctorDesk's own system. Brand hue remains open pending the Today visual pilot.

**A2. Brand color**

- [ ] Kill `--color-brand-*` as an indigo ramp. Choose one owned primary hue and defend it in writing against the brief "calm, clinical, trustworthy, Philippine private clinic, used 8 hours a day under fluorescent light."
- [ ] Author the ramp in **OKLCH**, not hex, as three explicit curves (T2). A workable lightness ladder for 50→950 is `0.985, 0.965, 0.925, 0.870, 0.780, 0.680, 0.585, 0.500, 0.420, 0.340, 0.230`; chroma humps in the middle and tapers at both ends; hue stays near-constant.
- [ ] **Anchor the chosen brand color at the step where its actual lightness falls.** Do not force it to be step 500 and rebuild the ramp around that, which distorts everything else.
- [ ] Note the one caveat on OKLCH: its gamut mapping degrades at extreme wide-gamut values. Irrelevant for an sRGB/P3 web app, so not a reason to avoid it here.
- [ ] Constrain primary usage: it marks _the_ action and _the_ active nav item, and nothing else. Today it also paints every waiting-room card button, every KPI icon chip, the logo tile, the assistant FAB, and selection highlights, which is why the UI looks like a blue template.
- [ ] Add a second accent only if a real need exists (e.g. distinguishing "clinical" from "administrative" contexts). Default answer is no.

**A3. Neutrals and surfaces**

- [ ] Replace the unmodified Tailwind gray ramp with an owned neutral ramp **derived from the brand hue** at ultra-low chroma (~0.004–0.012 OKLCH). Pure-neutral grays are a template tell; a tuned neutral is how Linear, Stripe, and Height read as "theirs."
- [ ] Aim for a theme defined by a handful of **source** variables that generate the rest. Linear's redesign reduced their theme definition from 98 variables to three (base color, accent color, contrast) by working in LCH. DoctorDesk currently hand-maintains far more than three, which is why the ramps drifted from each other in the first place.
- [ ] Keep semantic colors (success / warning / danger / info) on fixed hues but run them through the **same** lightness and chroma curves as the brand ramp, so they sit in the same world.
- [ ] Define an explicit **surface elevation scale** (canvas → sunken → panel → raised → overlay) with a real luminance step at every level, in both themes.
- [ ] Dark mode: delete `--card: rgba(255,255,255,0.03)`. Cards need a genuinely lighter surface than the page, so depth comes from luminance and borders become optional rather than load-bearing.
- [ ] Light mode: stop using a single `#f9fafb` page / `#ffffff` card pair for everything. Decide where the app is white-on-gray and where it is gray-on-white, and be consistent about which means "content" and which means "container."

**A4. Typography**

- [ ] Keep IBM Plex Sans (it is a defensible, non-default choice) but stop shipping Tailwind's default type scale. Author an explicit scale with per-step size, line-height, weight, and letter-spacing. Negative tracking on large text, slightly positive on small caps-y labels. Ratio at or below 1.25, with the small end hand-tuned rather than derived, since ratio math breaks below ~14px.
- [ ] Consider shipping **two scales rather than one compromise scale**, which is what IBM Carbon does (Productive vs Expressive). DoctorDesk has a dense staff dashboard _and_ a public booking page plus a marketing surface in one repo, and forcing both through one scale is why page titles are currently 20px. Shopify Polaris runs 14px as its primary body size specifically for admin density.
- [ ] Verify whether IBM Plex exposes an `opsz` axis, and check its numerals for **uniwidth** (digits keeping the same perceptual width across weights). Without uniwidth, bolding a figure in a table shifts the whole column, which is exactly the kind of jitter that reads as unfinished.
- [ ] Define the actual hierarchy the app needs: page title, section title, card title, body, label, caption, numeric-display. Right now page titles are `text-xl sm:text-2xl` and card titles are `text-base`, a 20→16px range that carries the entire hierarchy of the product.
- [ ] **Tabular numerals everywhere numbers align or change.** Currently 18 occurrences in the whole app. Every table cell with a number, every currency figure, every count, every time, every countdown must be `tabular-nums` or numbers will visibly jitter. This one change does more for "professional" than any layout edit.
- [ ] Set `font-variant-numeric` and optical sizing at the base layer so it is opt-out, not opt-in.
- [ ] Give currency a single formatter and a single visual treatment (alignment, decimal handling, negative/credit style). Billing currently renders peso values several ways.

**A5. Product mark**

- [ ] Design a real DoctorDesk mark. Any custom SVG drawn for this product beats `Stethoscope` in a rounded square, even a simple geometric monogram.
- [ ] Design a wordmark treatment (weight, tracking, optical alignment against the mark).
- [ ] Replace all four current logo sites: `AppSidebar.tsx` (expanded + collapsed), `AuthLayout.tsx`, `routes/index.tsx`.
- [ ] Ship favicon, PWA icons (maskable included), and an apple-touch-icon from the same mark.
- [ ] Define how a clinic's own logo (already supported via `clinics.logo_url`) coexists with the product mark in the sidebar, on PDFs, and on the public booking page.

**A6. Radius, border, shadow**

- [ ] Pick a radius _philosophy_ and apply it with intent instead of `rounded-2xl` on every container. Nested radii must be optically corrected (an inner element inside a 16px-radius parent with 16px padding needs ~8px, not 16px).
- [ ] Reduce border reliance. Right now nearly every boundary in the app is a 1px `--border` line, which is what makes screens look like wireframes. Replace many with surface-color changes or spacing. Linear's own redesign write-up describes the same problem in their product ("dividers had quietly proliferated across the platform, sometimes appearing without clear reason") and the fix was **softening their contrast**, not adding more of them.
- [ ] Rebuild the shadow scale so it is physically coherent (consistent light direction, a real ambient + direct pair, tinted with the neutral hue rather than `rgba(16,24,40,...)` inherited from the template).
- [ ] Focus rings: one owned focus treatment, visible on every surface in both themes, tested with keyboard-only navigation.

### Workstream B — Hierarchy and density system

The point: end card soup. A screen should have one focal point, and containers should earn their chrome.

**B1. Replace the single `Card` with a surface system**

- [ ] Introduce explicit surface variants mapped to the A3 elevation scale, e.g. `plain` (no border, no shadow, just spacing), `panel`, `raised`, `overlay`. Make `plain` the default so chrome is opt-in.
- [ ] Make `CardHeader`'s `border-b` opt-in. A divider under every single card title is a major contributor to the boxed-in look.
- [ ] Audit all 99 `<Card>` usages. The large majority should become sections defined by typography and whitespace, not bordered boxes. Target: fewer than 30 bordered surfaces in the app.
- [ ] Settings is the extreme case (25 cards). Convert it to a settings-row pattern: label/description left, control right, hairline separators, grouped under plain section headings. Nobody's settings page should be a stack of 25 identical boxes.

**B2. Establish one focal point per screen**

- [ ] For each of the 46 pages, write down in its route guide what the single most important element is, then make it visually dominant through size, weight, and position (not color alone).
- [ ] Establish a rule that sibling containers on one screen must differ in visual weight unless they are genuinely a repeating set of peers.
- [ ] Choose **one layout primitive and repeat it until it is the product's signature.** Across the sources this was the single highest-leverage discipline separating the clean 46% from the slop 54% in the quantitative audit (§3.2): one strong primitive everywhere beats seven card treatments and three stat banners. For an operational clinic tool the obvious candidate is a dense, divider-separated row that scales from the queue to the schedule to the patient list to the attention list. Decide it explicitly and commit.

**B3. Density**

- [ ] Define density as a **mode** with explicit row heights (roughly 32 / 40 / 48px), chosen per surface _and_ per breakpoint. Tables and the calendar get compact on desktop; forms and confirms get comfortable; mobile stays comfortable so the 44px rule holds. This is how the density-vs-touch-target conflict is resolved rather than averaged (§3.6).
- [ ] Lean deliberately on the WCAG 2.5.8 Spacing exception on desktop, and expand hit areas beyond visual bounds, so compact rows still conform.
- [ ] Treat clinician preference as settled evidence, not taste: surveyed clinicians preferred abbreviated text (57%) and color-coding (60%) over verbose descriptors (15%), and 63% asked for _more_ clinical abbreviations specifically to raise information density (§3.4). Density is the requirement; the current airy layout is the defect.
- [ ] Replace the flat `gap-4` rhythm (71 occurrences) with a spacing scale that encodes relationship: tight within a group, wider between groups, widest between sections. Uniform gaps are why everything reads as equally related.
- [ ] Row heights, cell padding, and line-heights set per density token, not per page.

**B4. Tables as the primary data surface**

- [ ] Table header: quieter than the data. Currently headers and cells compete.
- [ ] Numeric columns right-aligned with tabular numerals; text columns left; no centered data columns.
- [ ] Sticky header on scroll; sticky first column on mobile where a table survives.
- [ ] Row hover, keyboard focus, and selected states that are distinguishable from each other.
- [ ] Zebra striping: decide once, globally, and apply it (or not) consistently.
- [ ] Column-level empty values get one consistent treatment, not a mix of `—`, `No contact`, and blank.

**B5. Rethink the list chrome**

- [ ] Drop view modes nobody needs. The patients "grid" of cards is the clearest example; audit each list's three modes and keep only what has a real use.
- [ ] Make `ManagedList` chrome conditional on list size. A list with 6 rows should not render search + sort + per-page + view switcher + pagination + "Showing 1–6 of 6."
- [ ] Filters: move from a generic "Refine" popover toward visible, domain-specific filter chips for the ones that matter (doctor, date, status) with the long tail behind a menu.

### Workstream C — Iconography and status language

**C1. Icon strategy**

- [ ] Decide and document the icon system: stay on Lucide with strict rules, or move to a more considered set (Phosphor's weight axis suits a dense UI). Either way, one set, no mixing.
- [ ] Set optical rules: icon size tied to the cap-height of adjacent text, consistent stroke weight per context, optical centering by **center of gravity** rather than bounding box, `aria-hidden` on decorative icons.
- [ ] Fix a live bug: resizing a stroke-based icon does **not** change its stroke relative to the viewBox, so the app's `size-3` icons render visually bolder than its `size-5` ones. DoctorDesk renders Lucide at `size-3`, `size-4`, `size-5`, and `size-[18px]`, so this inconsistency is already shipping. Lucide's `absoluteStrokeWidth` prop keeps the on-screen stroke constant regardless of size.
- [ ] If staying on Lucide, override its defaults deliberately rather than accepting them: an off-default stroke (Lucide ships 2, Phosphor regular is 1.5, so something like 1.75 reads as chosen), a non-24px base size, and a color that is not `text-muted-foreground`. Leaving all three at default is a documented part of the shadcn fingerprint.
- [ ] Apply Lucide's own icon-design rules to any custom mark drawn for this product: 24×24 canvas, ≥1px padding, 2px centered strokes, round caps and joins, 2px between distinct elements, corner radii 2px above 8px and 1px below, and their optical-volume blur test (place it beside `circle` and `square`, blur all three; yours should not read darker).
- [ ] Reduce the icon count from 109 distinct icons **in nav and chrome only**. Most appear once or twice, which means they decorate rather than communicate.
- [ ] Do **not** thin out icons on clinical surfaces. The research is explicit that a healthcare team which collapsed calendar alerts into two icons behind a tooltip made staff hunt for information while a patient waited (§3.4, §3.6). Calendar blocks, queue cards, and the patient header should carry a **richer** alert vocabulary than they do now.
- [ ] Build the legend that makes clinical icon density work. Every icon on a calendar block or queue card maps to exactly one documented meaning, and the legend is reachable from that surface.

**C2. Kill literal metaphors**

- [ ] `Stethoscope` as logo → the A5 product mark. Three call sites plus the landing page.
- [ ] `Armchair` for waiting room → replace with a queue/list representation, or with a live count. Two call sites, both primary navigation.
- [ ] `Bot` for the assistant FAB and `Sparkles` for AI affordances → a custom mark for the assistant. The assistant is a flagship feature, so it deserves a drawn identity rather than the two most overused AI clip-art glyphs.
- [ ] `PhilippinePeso` as a decorative icon → remove; the formatted value already carries the currency.
- [ ] Add a rule: no icon may be a literal picture of a physical object standing in for an abstract concept.

**C3. Status encoding**

- [ ] Redesign appointment/visit status display. Today every status is a pastel-50 pill with -700 text, so all statuses have identical shape and weight and must be read rather than scanned.
- [ ] Use a multi-channel encoding so status survives color-blindness and grayscale: distinct shape per state (filled / outline / crossed), plus text, plus weight. Terminal/negative states (Cancelled, No Show) visibly recessive; live states (Arrived, In Consultation) prominent. CVD affects roughly 1 in 12 men.
- [ ] **Remove red from the appointment-type / categorical palette entirely**, so a type color can never be confused with a status color. DoctorDesk renders both on the same calendar, which is exactly the case NHS Scotland's design system structures around (§3.4).
- [ ] Design the status **transition**, not just the status. Nurses in a comparative study did not initially notice a colour change, so a state change gets a shape change or a brief motion cue. This is a safety requirement, and it is the one place in this product where new motion is justified on grounds other than polish.
- [ ] Document a threshold definition per status and use the same term for it in the calendar, the table, and the badge.
- [ ] Verify every status color against WCAG contrast in both themes. Pastel-50 fills with -700 text often fail at 12px.
- [ ] Doctor identity color coding for the calendar and waiting room, generated deterministically from doctor ID against a curated, accessible palette (not random hues).

**C4. People**

- [ ] Add avatars/initials for patients and doctors in lists, the queue, and the chart header. Deterministic initial colors from a curated palette. This single addition does more to make a patient list feel like a real product than any other change.
- [ ] Decide the patient-identity block once (name, age/sex, patient number, DOB) and reuse it everywhere a patient is referenced.

### Workstream D — Screen-by-screen redesign

Each screen gets: a hierarchy decision, real domain data, correct density, and its route guide updated in the same change (`.cursor/rules/route-guides.mdc`).

**D1. First impressions**

- [ ] `routes/index.tsx` — decide what this route is for. If it is a marketing landing page, design one. If the product has no public marketing surface yet, redirect authenticated users to `/dashboard` and unauthenticated to `/login` and delete the placeholder rather than shipping a stethoscope on a blank page.
- [ ] `AuthLayout` / login / register / forgot / reset / verify — redesign as a considered entry: real mark, a composed layout (not a centered `max-w-sm` box), correct autofill/password-manager behavior, visible-password toggle, inline error placement that does not shift layout, and a proper first-run path for a clinic that has just signed up.
- [ ] Onboarding — review the `Stepper` flow end to end. This is the moment a clinic decides whether the product feels serious.

**D2. Today (`/dashboard`)**

- [ ] Reframe from "KPI dashboard" to "day-of operations screen." The question it answers is "what do I do right now," not "how is the business doing."
- [ ] Delete `DashboardKpiRow` in its current form. Replace with a compact, non-card status line (queue count, next appointment, anything overdue) that does not occupy a full grid row of pastel chips. Linear's redesign named this exact move: it "reduces icon usage, scales their sizes down, and **removes unnecessary visual treatments like colored team icon backgrounds**."
- [ ] Make the schedule/queue the dominant element, not one of seven equal cards.
- [ ] Resolve the `TodayScheduleCard` / `WaitingQueueCard` duplication. One surface owns "who is here and what is next"; the other is removed or re-scoped so the same appointment never renders twice on one screen.
- [ ] Collapse the four identical `AttentionCards` into one prioritized "needs attention" list with typed rows, real counts (`+N more`, not a silent `.slice(0, 5)`), and rows that deep-link to the specific record rather than a list page.
- [ ] Move the 14-day appointments trend chart to Insights. A trend chart is a reporting artifact, not a front-desk tool.
- [ ] Role-differentiate: a doctor's Today and a receptionist's Today should not be the same screen with items hidden.

**D3. Schedule (list + calendar)**

- [ ] Calendar is the real product surface here; make it the default view, not a tab next to a list.
- [ ] FullCalendar styling pass: event chips, current-time indicator, working-hours vs closed shading, doctor color coding, overlap handling, all-day/blocked time. Borrow the verified patterns from §3.4: appointment **type** by color, alerts by block **style**, unavailable time as solid untitled grey, and appointment blocks never exceeding 50% of column width so overlaps stay readable.
- [ ] Adopt Jane App's figure/ground inversion: give **bookable shift time a tinted background and leave unavailable time plain white**, so the eye reads bookable time as the figure.
- [ ] Add a **pop-out** for appointment detail rather than navigating away, and include the fields staff need while the patient is standing there: phone, email, balance, and next scheduled visit. That last point is a post-launch lesson from the Athelas case study, not a guess.
- [ ] Target 5+ providers visible at once on desktop. This is the "birds eye view of the day ahead" that clinical staff ask for and that the current padding prevents.
- [ ] Day view for the front desk; week view for planning; resource/doctor columns for multi-doctor clinics.
- [ ] Add a keyboard density control in the spirit of Jane's number keys 1–7 setting how many upcoming days are shown. Cheap, and their docs call it a staff favourite.
- [ ] Appointment event content must be legible at real density (patient, time, type, status) without hover, since tablets have no hover.
- [ ] `AppointmentNewPage` (402 lines) — form craft pass: logical grouping, conflict feedback shown inline at the moment of choosing a slot rather than on submit, slot picking instead of raw time entry, recurring-series scope choices stated in plain language.

**D4. Waiting room**

- [ ] Add **elapsed wait time** per patient, live, with a visual escalation as it grows. This is the primary missing datum.
- [ ] Add patient identity (avatar/initials, age/sex), appointment type, and assigned doctor color.
- [ ] Fix the button storm: one primary advance action per column context, secondary actions demoted or in an overflow. Nine identical blue buttons is not a queue.
- [ ] Column headers carry live counts and, where useful, aggregate wait (longest wait in column).
- [ ] Replace `Empty` with a real empty state per column.
- [ ] Tablet-landscape layout as a first-class target; this screen lives on a shared tablet at the front desk.
- [ ] Verify the WebSocket-driven updates animate in a way that does not lose the user's place.

**D5. Patients**

- [ ] Rebuild the list columns around what identifies and prioritizes a patient: avatar + name, age/sex, patient number, last visit, next appointment, outstanding balance, and flags (allergy, HMO). Remove the grid view.
- [ ] Search results should show enough to disambiguate two patients with the same name.
- [ ] `PatientDetailPage` (1044 lines) — this is the chart, the most important screen in the product for a doctor. Full information-architecture pass: a **persistent patient context rail** (identity, allergies, balance, flags) in the spirit of Epic's Storyboard, then the chart body. Timeline vs tabs decision. Allergies and alerts must be impossible to miss.
- [ ] Consider a patient-centric scheduling hub distinct from the calendar, which is what Epic's Appointment Desk is (§3.4): demographics, insurance, appointment history, future appointments, all in one place with filterable tabs. Front desk starts most scheduling from the patient, not from the grid.
- [ ] The named failure mode to design against is **information sprawl**: scattering one patient's story across screens and categories. Consolidate rather than adding tabs, and eliminate low-traffic tabs from the default view.
- [ ] Where the chart collapses information, make the collapse **visible and labelled**. 23% of surveyed clinicians said they would not trust a system's hiding rules and 56% require an indicator of what type of information is hidden (§3.4).
- [ ] Chart sub-surfaces (visits, prescriptions, documents, billing) get consistent structure rather than per-page invention.

**D6. Clinical (SOAP)**

- [ ] `SoapNotePage` (580 lines) — writing surface craft: this is where a doctor types for minutes at a time. Measure line length, comfortable line-height, autosave state that is visible but not noisy, version history that is reachable without leaving the note.
- [ ] Distinguish the four SOAP sections structurally without wrapping each in a bordered card.
- [ ] AI draft affordances (transcription, draft SOAP) must read as draft-pending-review, with a distinct visual state from a clinician-authored note, per `ai-assistant-safety.mdc`.

**D7. Billing**

- [ ] Currency alignment and tabular numerals across invoices, claims, eligibility, LOA.
- [ ] Invoice detail and the printed/PDF invoice should share a visual language; a receipt a patient holds is a brand surface.
- [ ] Payment state (paid / partial / overdue / void) needs unambiguous, non-pastel encoding.
- [ ] Claims and LOA screens: reduce from generic table-plus-chrome to a workflow view that shows where each claim is stuck.

**D8. Documents, Insights, Settings, Platform**

- [ ] Documents generate/templates: template editor and preview need to look like the printed output.
- [ ] Insights/Reports: chart styling pass (ApexCharts theme bridge), correct axis formatting, no chart junk, no gratuitous chart types, empty and single-data-point states.
- [ ] Activity log: dense, scannable, monospace where it helps; this is an audit surface and should look like one.
- [ ] Settings: the B1 settings-row conversion, plus grouping review across 11 settings pages.
- [ ] Platform/super-admin: deliberately distinct from clinic UI so an operator never confuses the two contexts.

**D9. AI assistant surface**

- [ ] Replace the `Bot` FAB with the C2 assistant mark, and reconsider a floating circle as the entry point on desktop (a docked panel or command-palette integration may be better).
- [ ] Delete the `localStorage`-gated hint bubble ("Ask to book, check a balance, or cancel a visit.") or replace it with a real first-run affordance inside the panel.
- [ ] Tier 2 confirm cards are the highest-stakes UI in the product: they need to look unmistakably like a decision point, with the entity name prominent, the diff/proposal legible, and Confirm/Send visually distinct from routine buttons.
- [ ] Streaming/thinking states, tool-call display, and error states all need designed treatments. The pattern worth copying is Nabla's: make the model's **in-progress reasoning visible and interruptible** rather than a spinner followed by a finished block (§3.4). This strengthens the existing Tier-2 draft-then-confirm model rather than competing with it.

**D10. Cross-cutting states**

- [ ] Empty states: currently icon + one line, centered, at three sizes. Give the important ones (no patients, no appointments today, empty queue) real design and a genuinely useful action.
- [ ] Error states: distinguish network failure, permission denied, and not-found. `ForbiddenPage` should not look like a crash.
- [ ] Loading: audit the skeletons against the new layouts; a skeleton that does not match the loaded markup causes layout shift, which reads as cheap.
- [ ] Toasts: verify the Sonner override still works with the new tokens; confirm placement does not cover the bottom tab bar on mobile.
- [ ] Command palette: this is a craft showcase surface (Linear/Raycast set the bar). Grouping, recents, keyboard hints, result density.

### Workstream E — Native mobile feel

**E1. Motion retune**

- [ ] Reduce `DURATION_PAGE_S` from 300ms. Target ~120–180ms for route changes, or drop the page transition and animate only changed content.
- [ ] Re-tune `SLIDING_PILL_SPRING` and sheet physics against real device feel rather than chosen numbers. Reference curves worth starting from: `ease-out: cubic-bezier(0.23, 1, 0.32, 1)`, `ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`, and for an iOS-feeling drawer `cubic-bezier(0.32, 0.72, 0, 1)`. Swipe-dismiss velocity threshold around 0.11 (drag distance over elapsed time). Keep any masking blur under 20px, since heavy blur is expensive in Safari.
- [ ] Audit `framer-motion` usage for the `x`/`y`/`scale` shorthands, which are **not** hardware-accelerated (they run on the main thread via rAF). Use the full `transform` string on anything performance-sensitive.
- [ ] Audit every animation for whether it earns its duration. Motion should confirm causality, not perform.
- [ ] Keep every `prefers-reduced-motion` path intact (this is already correct; do not regress it).

**E2. Gesture and touch**

- [ ] Swipe-back navigation on phone.
- [ ] Review `SwipeRevealRow` friction, thresholds, and rubber-banding against iOS behavior.
- [ ] Haptics via the Vibration API on confirm/destructive actions where supported. Strictly progressive enhancement: iOS Safari has no support, so it can never be load-bearing feedback.
- [ ] Consider View Transitions for the shell, as progressive enhancement only. Same-document transitions reached Baseline in Oct 2025, but Firefox stable still lacks cross-document support, so unsupported browsers must simply navigate normally.
- [ ] Remove any affordance that only appears on hover, since tablets have no hover. Audit all `hover:` styles for touch equivalents.
- [ ] Scroll: momentum, overscroll containment in sheets, scroll position restoration on back navigation.

**E3. Shell**

- [ ] Bottom tab bar craft: active-state transition, icon/label alignment, badge counts (queue size, unread alerts), correct safe-area inset.
- [ ] Revisit the 4-tab split (Calendar / Waiting / Patients / More) against what staff actually do on a phone.
- [ ] `MobileMoreSheet` should not be a dumping ground.
- [ ] Header on mobile: it currently spends its width on a search field. Give it page context instead.
- [ ] Sheet craft: drag handle feel, dismiss thresholds, stacked sheets, keyboard avoidance when a text field is focused inside a sheet. Evaluate the current approach against the technique the field has converged on: a real `<dialog>` in the top layer over a **CSS `scroll-snap` container whose snap stops are the detents**, so 1:1 tracking, momentum, and rubber-banding run on the compositor and there is no drag loop to have bugs in. Springs compile to a CSS `linear()` timing function. The specific hard case to test is the scroll-to-drag handoff: when scrollable sheet content reaches the top and the user keeps pulling, the sheet must follow the finger.
- [ ] Handle the on-screen keyboard through `visualViewport` resize **and** scroll events, and focus controls with `preventScroll`, rather than fixed-position workarounds.

**E4. Installed/standalone**

- [ ] Standalone-mode audit: status bar treatment, theme-color per theme, splash screen, no browser-chrome assumptions.
- [ ] Tablet landscape as a designed layout for calendar, waiting room, and chart, not just "desktop, narrower."
- [ ] Verify no horizontal page scroll at 375px on all 46 pages.
- [ ] Verify 44×44px minimum on every control, including table row actions and calendar events.

### Workstream F — Copy pass

- [ ] Resolve the `design-system.md` §12 vs `ui-minimal-copy.mdc` contradiction in favor of the minimal-copy rule. Remove "every page carries a description" as a requirement.
- [ ] Make `PageHeader`'s `description` genuinely optional and delete the ones that restate the title. Review all 40 `description` call sites across the 29 pages that use `PageHeader`.
- [ ] Rewrite the six `SectionHub` descriptions in `nav-config.ts` or delete them.
- [ ] Audit every string against `human-copy.mdc`: no em dashes, no "This lets you…", no marketing adjectives, no padded helper text.
- [ ] Audit `FORM_PLACEHOLDERS` for placeholder text that duplicates its label.
- [ ] Empty-state and error copy: state what happened and the next step, nothing more.
- [ ] Assistant response copy: answer first, no preamble.

### Workstream G — Anti-slop rules, skills, and enforcement

This is the part that keeps the result from decaying. Without it, the next agent session re-introduces a pastel KPI card.

- [x] Write `.cursor/rules/anti-slop-design.mdc` — glob-scoped to `apps/web/**/*.tsx` and `apps/web/src/styles.css`, holding the §2 rule set as hard pass/fail assertions.
- [x] Record a **baseline** of mechanical slop counts (`docs/workflow/baselines/design-slop-baseline.json`, ratchet in `check:design-slop`). Phase 42a stored the pre-overhaul quantitative audit by hand; the checker lands in Phase 43.
- [x] Write `.agent/skills/design-review/SKILL.md` — the §2.8 procedure. Symlink into `.cursor/skills/` and `.claude/skills/` per the repo's skill convention.
- [x] Add a `design-reviewer` subagent to `.cursor/agents/` (alongside the existing `debugger`, `security-auditor`, `test-runner`, `verifier`) that runs the rubric against a diff or a route and returns a pass/fail report with file:line violations.
- [x] Add a `/dd-design-review <route>` command to `.cursor/commands/` and list it in `dd-help.md`.
- [x] Add `scripts/dev/check-design-slop.sh` + a `check:design-slop` package script, following the existing `check:filenames` pattern. Design it the way the one quantitative slop audit was designed (§3.2): **deterministic checks on computed styles and AST**, no LLM judging, since LLM screenshot-grading reintroduces the bias being measured. Expect ~5–10% false positives and make the checker's output easy to override with a written reason. Covers the mechanically-checkable rules: banned icon names (B3/B4/B5), new `rounded-2xl border shadow` triples (H3), numeric cells without `tabular-nums` (T9), hardcoded hex outside `styles.css` (T11), new `PageHeader description` props (B7), `hover:` styles with no touch equivalent (M6). Wire it into `pnpm run ci:quality`.
- [x] Rewrite `DESIGN.md` as the principle-level source of truth for the new system, replacing TailAdmin references.
- [x] Create `docs/architecture/design-language.md` as the authoritative token + component spec (A1). Brand hue remains open; waiting-room layout is closed.
- [x] Demote `docs/architecture/design-system.md` to a historical audit of a studied template.
- [x] Update `.cursor/rules/components.mdc`, `motion.mdc`, and `mobile-responsive.mdc` for the new surface system, motion timings, and touch rules.
- [x] Build a screenshot harness on the existing Playwright setup (`apps/web/e2e/design-screenshot-harness.spec.ts`, `pnpm run capture:design-screenshots`) that logs in with seed data and captures listed routes at 375 / 820 / 1440px in both themes. Not part of default `test:e2e`. Output goes to gitignored `.audit-screenshots/harness/`.
- [x] Update `.cursor/rules/README.md`, `.claude/README.md`, `.opencode/README.md` indexes, and run `pnpm run check:ai-tooling-sync`.

### Workstream H — Accessibility and quality gates

- [ ] Contrast audit of every token pair in both themes against WCAG 2.2 AA (4.5:1 body, 3:1 large text and UI boundaries). Pastel badge fills are the likeliest failures.
- [ ] WCAG 2.2 target size (2.5.8) verification alongside the existing 44px rule.
- [ ] Keyboard-only pass through the core flows: book an appointment, arrive a patient, write a SOAP note, take a payment. Visible focus at every step, no traps, logical order.
- [ ] Screen-reader pass on the shell, tables, dialogs/sheets, and the assistant panel: live-region announcements for queue updates and toasts.
- [ ] Reduced-motion, forced-colors, and 200% zoom passes.
- [ ] Dark mode parity check on every screen, since the template's dark surfaces are being replaced.

---

## 5. Phase mapping

Latest shipped phase is 41, so this becomes Phases 42–47. Each needs a phase file written before coding, per `docs/phases/README.md`.

| Phase | Title                                                                                                           | Workstreams | Depends on |
| ----- | --------------------------------------------------------------------------------------------------------------- | ----------- | ---------- |
| 42    | Baseline, 3 brand candidates piloted on the waiting room, staff validation, then ratify the token system (§5.1) | A           | 31         |
| 43    | Anti-slop rules, design-review skill, screenshot harness                                                        | G           | 42         |
| 44    | Hierarchy and density system (end card soup)                                                                    | B, C        | 42         |
| 45    | Screen redesign: shell, entry, Today, Schedule, Waiting room                                                    | D1–D4, F    | 44         |
| 46    | Screen redesign: Patients, Clinical, Billing, Documents, Insights, Settings, Assistant                          | D5–D10, F   | 44         |
| 47    | Native mobile feel + accessibility gates                                                                        | E, H        | 45, 46     |

Phase 43 lands early on purpose: the rubric and the screenshot harness must exist before the bulk of the redesign, so every screen in 45/46 is graded as it ships rather than audited afterwards.

### 5.1 Pilot-first shape (decided, §8.1)

The table above is the rollout sequence. It does **not** start until a waiting-room pilot has been built and validated. Phase 42 is therefore split:

**Phase 42a — Baseline.** Before a single token changes, capture the app as it stands: screenshots of every route at 375 / 820 / 1440px in both themes, plus the rule-sweep and deterministic-checker counts, stored. This is the only way to demonstrate later that the overhaul worked rather than asserting it. If the full harness is too slow to build first, capture manually and record counts by hand, but capture something. Everything after this point is measured against it.

**Phase 42b — Three candidate directions, one screen.** Build the waiting room three times, fully rendered, one per brand direction (§8.1), each with an owned token set, the hierarchy system applied, real elapsed wait times, and a written rationale plus contrast audit. Deliberately not a mockup: a rendered screen against real seed data is the only artifact that answers the question.

**Phase 42c — Validate with staff.** Put the candidates in front of real front-desk users against the success bar agreed in §8.2 decision 7. Record which direction wins and why.

**Phase 42d — Ratify the system.** Only the winning direction becomes `design-language.md` and `styles.css`. The other two are archived with their rationales so the rejected alternatives stay on record, which is what §2.0 requires of every decision.

Then 43 → 44 → 45/46 → 47 as tabled, with the pilot's waiting room as the reference implementation every other screen is measured against. If the pilot fails its success bar, the rollout does not start; the direction is reworked at the cost of one screen instead of forty-six.

One consequence worth stating plainly: the rubric (Phase 43) is _used_ during the pilot before it is formally shipped. Draft it early enough to grade the three candidates, then harden it into the rule, skill, and subagent once the pilot has stress-tested it. A rubric written without ever having been applied is the same failure mode as a token set adopted without ever having been chosen.

---

## 6. Docs to update

| Doc                                                                   | Change                                                                                                                                                                                                                       |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DESIGN.md`                                                           | Rewritten as the principle-level source of truth for the new system; all TailAdmin references removed                                                                                                                        |
| `docs/architecture/design-language.md`                                | **New.** Authoritative token + surface + component spec                                                                                                                                                                      |
| `docs/architecture/design-system.md`                                  | Demoted to a historical audit; §3.2/§11 reversal explicitly revoked; §12's "every page carries a description" removed; the §11.2 reference to a "design-quality hook" deleted, since no such hook exists in `.cursor/hooks/` |
| `docs/guides/routes/**` (41 guides)                                   | Per-screen behavior/hierarchy updates alongside each D-workstream change, per `route-guides.mdc`                                                                                                                             |
| `docs/guides/routes/README.md`                                        | Progress overview refreshed                                                                                                                                                                                                  |
| `.cursor/rules/anti-slop-design.mdc`                                  | **New.** The rule set from §2                                                                                                                                                                                                |
| `.cursor/rules/components.mdc`                                        | Surface system replaces single-Card guidance                                                                                                                                                                                 |
| `.cursor/rules/motion.mdc`                                            | Retuned durations                                                                                                                                                                                                            |
| `.cursor/rules/mobile-responsive.mdc`                                 | Gesture, haptics, hover-free affordance rules                                                                                                                                                                                |
| `.cursor/rules/ui-minimal-copy.mdc`                                   | Note that it now wins the page-description conflict                                                                                                                                                                          |
| `.cursor/rules/README.md`, `.claude/README.md`, `.opencode/README.md` | Index the new rule, skill, subagent, command                                                                                                                                                                                 |
| `.agent/skills/design-review/SKILL.md`                                | **New.** Critique procedure                                                                                                                                                                                                  |
| `.agent/skills/components/`, `motion/`, `mobile-responsive/`          | Aligned with the new system                                                                                                                                                                                                  |
| `docs/phases/phase-42..47-*.md`                                       | **New.** One file per phase                                                                                                                                                                                                  |
| `docs/phases/README.md`                                               | Status table rows for 42–47                                                                                                                                                                                                  |
| `docs/mvp.md`                                                         | Only if a screen's scope changes (e.g. dropping list view modes)                                                                                                                                                             |

---

## 7. Acceptance gates

The plan is done when an outside designer looking at the app cannot identify the template it came from. Concretely:

**Token-level**

- [ ] No hex value in `styles.css` traceable to TailAdmin or Tailwind defaults; brand ramp authored in OKLCH.
- [ ] Type scale, radius scale, and shadow scale are all explicitly authored, not inherited.
- [ ] Contrast audit passes WCAG 2.2 AA on every token pair in both themes.

**Component-level**

- [ ] Fewer than 30 bordered/shadowed surfaces in the app (from 99).
- [ ] Zero pastel-tinted icon chips in KPI or stat positions.
- [ ] No `Stethoscope`, `Armchair`, `Bot`, or `Sparkles` anywhere in `apps/web`.
- [ ] A custom product mark and a custom assistant mark exist as real SVGs.
- [ ] Every numeric cell and currency figure uses tabular numerals.

**Screen-level**

- [ ] Every one of the 46 pages has a documented single focal point, realized visually.
- [ ] Waiting room shows live elapsed wait time.
- [ ] Patient list shows identity-disambiguating and prioritizing data.
- [ ] No page ships a description that restates its title.
- [ ] Red appears nowhere in the appointment-type palette, so a type color cannot be read as a status color.
- [ ] Every clinical status transition is legible without relying on the color change being noticed.
- [ ] No horizontal scroll at 375px; every control ≥ 44×44px.

**Density-level** (the measurable form of "professional, not airy")

- [ ] Desktop tables and the queue render at compact row heights, not the current comfortable default.
- [ ] The schedule shows 5+ providers at once on desktop.
- [ ] The dashboard fold is occupied by the schedule and queue, not by KPI chips and a trend chart.
- [ ] No screen relies on padding where a divider or spacing would do (H12 ladder applied).

**Process-level**

- [ ] A pre-overhaul baseline exists (screenshots + rule-sweep counts), and the post-overhaul counts are recorded against it.
- [ ] `anti-slop-design.mdc`, the `design-review` skill, and the `design-reviewer` subagent all exist and are indexed.
- [ ] Screenshot harness captures all routes at 3 widths × 2 themes.
- [ ] Every screen in Phases 45–46 passed a recorded design review before its phase was marked Done.
- [ ] `pnpm run ci:quality` green; `pnpm run check:ai-tooling-sync` clean.

---

## 8. Decisions

These are genuine forks that must not be resolved by an agent picking a default, since defaulting is the thing this plan exists to stop.

### 8.1 Resolved

**Sequencing: pilot first.** Run the full stack (owned tokens + hierarchy system + rubric) on the **waiting room alone**, put it in front of real front-desk staff, and only then roll the system across the remaining screens. The waiting room is the right pilot: it is the densest operational surface, it has a measurable success criterion (can staff answer "who has waited longest" faster than before?), and it is small enough to redo if the direction proves wrong. This supersedes the linear 42→47 reading of §5; see §5.1.

**Brand hue: explore before deciding.** Do not pick a hue from a description. Build **three candidate directions as real screens** (the same waiting room, fully rendered, in each) and decide from the rendered result. This is the §2.0 principle applied to the plan's own highest-impact decision: a hue chosen from a list of adjectives is still an unspecified default. Candidates to render, with anything in the indigo/violet family off the table:

1. Desaturated clinical blue-green. Trust signal without the SaaS-indigo association.
2. Deep navy-slate with one warm accent. Reads established and institutional.
3. A third direction proposed during the work, not pre-committed here, so the exploration is not a two-horse race with a foregone conclusion.

Each candidate ships with a written rationale against the brief ("calm, clinical, trustworthy, Philippine private clinic, viewed 8 hours a day under fluorescent light") and a full contrast audit, so the comparison is on evidence rather than preference.

### 8.2 Still open

| #   | Decision            | Notes                                                                                                                                                                                                                                                                                                                                       |
| --- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2   | Keep IBM Plex Sans? | It is already a defensible, non-default choice, and switching costs a load-performance pass. Recommendation: keep it, author a real scale around it. Alternative if a distinct voice is wanted: a grotesque with true tabular figures and a tighter clinical feel.                                                                          |
| 3   | Icon set            | Stay on Lucide under strict rules (cheapest, already installed) vs. move to Phosphor for its weight axis vs. license a considered set. Recommendation: stay on Lucide, add rules, and hand-draw the two marks that matter (product, assistant).                                                                                             |
| 4   | What is `/` for?    | Design a real marketing landing page, or redirect and delete the placeholder. This changes Phase 45's scope materially.                                                                                                                                                                                                                     |
| 5   | Who draws the mark? | An agent can produce a competent geometric monogram. A distinctive mark is a human designer's job. Decide whether to commission one or ship an interim monogram with a placeholder flag.                                                                                                                                                    |
| 6   | Density default     | Does the front desk want maximum rows visible (compact default, comfortable opt-in) or the reverse? Ideally answered by watching someone use it, not by preference.                                                                                                                                                                         |
| 7   | Pilot success bar   | What result from the waiting-room pilot justifies rolling the system out, and what sends it back? Agree this before building the pilot, or the review becomes a preference conversation. Suggested bar: staff answer "who has waited longest" and "who is next for Dr. Santos" faster than on the current screen, and prefer it unprompted. |

---

## 9. Non-goals

- No API, schema, or business-logic changes. This is entirely `apps/web` plus docs and agent tooling.
- No new features. Where a screen is missing data (elapsed wait time, patient balance in a list), the data already exists in the API; if it does not, that becomes a separate scoped item rather than growing this plan.
- No decorative motion, gradients, glassmorphism, bento grids, or illustration sets. "Professional" here means clinical confidence, not visual novelty. The existing prohibition in `motion.mdc` stands.
- No component-library migration. shadcn/ui + Radix + `cva` stays; what changes is the taste layer on top of it.
