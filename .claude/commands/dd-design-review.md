# dd-design-review

Run an anti-slop design review of $ARGUMENTS (a route path such as `/dashboard/waiting-room`, or `diff` for the current git diff).

1. Read `.cursor/rules/anti-slop-design.mdc` and `.agent/skills/design-review/SKILL.md`.
2. Run `pnpm run check:design-slop`.
3. If a route is given and the local app is running, capture screenshots (`pnpm run capture:design-screenshots`) at 375 / 820 / 1440 in light and dark. Output: `.audit-screenshots/harness/` (gitignored).
4. Follow the skill report format. At most six issues. File:line on every code finding.
5. Do not pick a brand hue. That decision is still open.

If `$ARGUMENTS` is empty, review the current git diff against `main`.
