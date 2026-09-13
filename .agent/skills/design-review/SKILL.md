---
name: design-review
description: >-
  Run a pass/fail anti-slop design review of a DoctorDesk web route or diff.
  Use before shipping UI, when asked to review a screen, or via /dd-design-review.
---

# Design review

Load this skill **and** `.cursor/rules/anti-slop-design.mdc` before writing a word of critique. The rubric must not silently go stale relative to the rule file.

Default to flagging. Approval is earned. A reviewer that finds nothing has not reviewed.

## Operating loop

1. **Capture.** Screenshot the surface at 375 / 820 / 1440px in both themes. Never review from code alone. Never review from screenshots alone. If the local app is up: `pnpm run capture:design-screenshots`. Output: `.audit-screenshots/harness/` (gitignored).
2. **Deterministic sweep first.** `pnpm run check:design-slop`. Anything a script can decide is not left to judgment.
3. **Squint test (H1, H5).** Blur: one entry point? Grayscale: does hierarchy survive?
4. **Template test.** Which template does this look like? Name the elements if the answer is specific.
5. **Decision audit.** The five most visually prominent choices: state the decision and the rejected alternative. Unanswered = slop.
6. **Rule sweep.** Walk T, H, B, I, D, C, M. Record each violation with `file:line`.
7. **Domain test (D1).** A front-desk-at-9am question: who has waited longest? which Juan Santos is this? what do I do next? If the screen cannot answer, it is a data problem, not a visual one.
8. **Report** in the format below.

## Report format

- At most **six** issues, ranked by visual impact. No padding. Two issues gets two, plus one line saying why the list is short.
- **Before / After / Why** per issue.
  - Before is a fact, never a feeling.
  - After must fit inside an hour of work. A rewrite is a separate finding.
  - Why is exactly one citation: a rule ID, a WCAG SC, or a named source. Never an uncited opinion.
- Statuses, not scores: `pass` / `fail` / `partial` / `not applicable` / `cannot tell from this artifact`.
- Durable-fix column: lint rule, token, primitive, or test that stops that _family_ of failure.
- Close by naming the **one** fix that matters most.
- Never an empty pass. A clean screen still gets two or three polish items.
- Banned words in the report: effectively, leverages, seamless, streamlined, optimises, robust, elevate.

First line if an AI-made-this test would succeed: say so, and name the three responsible elements.

## Remedial order

1. Delete
2. Reduce
3. Change the token
4. Change the component
5. Restructure the screen
6. Rebuild

## Ship criteria

Zero B-class. No unresolved H-class. Cost of the fix decides close calls.

Do not review in adjectives. State the rule, the surface, and the intended outcome.

## Brand hue

Hue is **not ratified**. Do not recommend "just pick teal" from this review. Token ratification happens on a rendered Today (`/dashboard`) pilot. See `docs/architecture/design-language.md`.
