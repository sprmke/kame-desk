---
name: design-system-extraction
description: Extract a concrete design system (colors, type, spacing, radius, shadows, motion, components, third-party libs) from a live reference site. Use when the user links a demo/competitor site and wants its design system documented or ported.
---

# Design system extraction from a live site

Turns "review this site's design" into a concrete, reusable spec instead of prose adjectives. Combines browser inspection with static asset analysis — computed styles alone miss the token _system_; the compiled CSS alone misses real rendered values. Use both.

Reference audit produced with this skill: `docs/architecture/design-system.md` (TailAdmin React demo → DoctorDesk).

## When to use

- User links a live site/demo and asks to "analyze the design system" or "extract the design for our app."
- Evaluating a template/theme before adopting it (e.g. an admin dashboard template).
- Competitive UI research where the deliverable is tokens + component inventory, not a screenshot gallery.

## Workflow

### 1. Crawl with the browser tool, not just the homepage

Use `cursor-ide-browser` (`browser_navigate` + `browser_take_screenshot`). Get real internal routes first instead of guessing slugs:

```js
// Runtime.evaluate via browser_cdp
JSON.stringify(
  Array.from(document.querySelectorAll("a[href]"))
    .map((a) => [a.textContent.trim().slice(0, 30), a.getAttribute("href")])
    .filter((x) => x[1] && x[1].startsWith("/")),
);
```

Visit one page per component family, not every page: dashboard/home, buttons, cards, badges/alerts, forms, tables, modals/dropdowns, a detail/profile page, an error page, and the dashboard again with dark mode forced on (see step 4). That's usually 8-10 pages, not 50.

### 2. Pull the compiled CSS and JS bundle with `curl`, not the browser

Static analysis is cheaper and more complete than clicking through every state:

```bash
curl -s -o styles.css "<link rel=stylesheet href>"
curl -s -o bundle.js "<script type=module src>"
```

Grep the CSS for custom properties — if it's Tailwind v4, tokens live as `--color-*`, `--text-*`, `--radius-*`, `--shadow-*`, `--spacing`, `--font-*`, `--breakpoint-*`, `--z-index-*` (`@theme` output). Extract with a script, not by eye — minified CSS puts hundreds of declarations on one line:

```python
import re
pairs = re.findall(r'(--[a-zA-Z0-9-]+):\s*([^;]+);', css)
```

Group by prefix (`color`, `text`, `radius`, `spacing`, `font`, `animate`, `ease`, `z`) and dedupe by keeping first occurrence.

Grep the JS bundle for library fingerprints instead of relying on `window.*` globals (ES module bundles rarely attach globals):

```bash
for term in apexcharts fullcalendar flatpickr swiper jsvectormap react-jvectormap \
  maplibregl clsx classnames framer-motion "@radix-ui" "@headlessui" simplebar nprogress; do
  grep -o -i -c "$term" bundle.js
done
```

Also check for `/*! ... */` license/webpack-comment banners — they often name the exact package (`@react-jvectormap/lib`, `jquery.jvectormap.min`, etc.) even when minified.

### 3. Get real rendered values via CDP, not just the source CSS

Compiled utility classes reference `var(--tw-shadow-color, ...)` — resolve what a _real element_ renders to confirm the token system matches shipped UI:

```js
// Runtime.evaluate, returnByValue: true
const cs = getComputedStyle(el);
({
  font: cs.fontFamily,
  size: cs.fontSize,
  weight: cs.fontWeight,
  padding: cs.padding,
  radius: cs.borderRadius,
  bg: cs.backgroundColor,
  shadow: cs.boxShadow,
  transition: cs.transition,
  height: cs.height,
});
```

Do this for: a primary button (each size variant), a card, the sidebar, the header — that's usually enough to confirm the spacing/radius/shadow scale and catch any drift between source tokens and what's actually shipped.

### 4. Force dark mode without hunting for the toggle

Check how the theme is persisted before clicking through the UI:

```bash
grep -o 'localStorage\.[a-zA-Z]*Item([^)]*theme[^)]*)' bundle.js
```

Usually `localStorage.getItem("theme")` / `setItem("theme", ...)` + a `.dark` class on `<html>`/`<body>`. Set both directly, then reload:

```js
localStorage.setItem("theme", "dark");
document.documentElement.classList.add("dark");
```

Faster and more reliable than finding and clicking the actual toggle button, and works even if the toggle is JS-state-only until reload.

### 5. Never trust `Page.navigate` via CDP for SPA crawling

Many CDP hosts deny raw `Page.navigate`/`Input.*` for security. Use the tool's own `browser_navigate` for routing; accept the larger snapshot payload as the cost of reliability, or fetch `href`s in bulk (step 1) to cut down the number of navigations needed.

### 6. Write the output as tokens + component inventory, not prose

Structure the deliverable so it is directly portable into a Tailwind/shadcn config, not just descriptive:

1. **Typography** — font family + source (Google Fonts vs self-hosted), weight scale, type scale with line-heights.
2. **Color** — full neutral ramp, brand/primary ramp, semantic (success/warning/error/info) ramps, each as hex/oklch with the source variable name. Note dark-mode remapping, not just "it has dark mode."
3. **Spacing & layout** — base unit, real measured values for sidebar/header/container, not just "generous padding."
4. **Radius** — the exact scale (e.g. `sm/md/lg/xl/2xl/3xl/full`) mapped to px.
5. **Shadows** — the named elevation scale with literal `box-shadow` values, not just "subtle shadow."
6. **Motion** — durations + easing curves actually used, and _which_ properties transition (color/bg/border/shadow/transform is a common bundle, not just "hover effects").
7. **Component inventory** — one line per component family with variant/size/state coverage observed (e.g. "Button: primary/secondary/outline × sm/md × with-icon-left/right").
8. **Third-party libraries** — name, purpose, confirmed via bundle grep, license (check before recommending — MIT/Apache/ISC are safe defaults, flag anything GPL/AGPL/commercial for the user to decide).
9. **Adoption notes** — explicit call-outs on what to keep vs. adapt vs. reject given the target app's own design principles (cite the target app's own `DESIGN.md`/brand rules). Extracting a design system is not a license to copy it verbatim — reconcile with the target product's tone (e.g. a clinical dashboard should not inherit a marketing template's decorative gradients or vivid brand hue, even if it inherits the spacing/shadow/radius _system_).

### 7. Respect the target repo's doc/skill conventions

Save the detailed audit under that repo's architecture docs (or equivalent), update its top-level design doc to reference it, and follow that repo's `documentation-maintenance` rule in the same change. Don't invent a new docs folder.

## Anti-patterns

- Screenshotting every single page instead of one per component family — burns tokens for no new signal once the pattern repeats.
- Reporting colors as swatches/descriptions only — always capture the literal hex/oklch value and the source token name.
- Copying a reference site's brand color/decorative elements wholesale into a product with an already-defined, different visual philosophy.
- Skipping the JS bundle grep — computed styles tell you _what_ renders, bundle grep tells you _which library_ is responsible, which is what you need to recommend (or avoid) a dependency.
