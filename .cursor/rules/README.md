# Cursor rules — DoctorDesk

After clone: `pnpm run setup:ai-tooling`.

## Always-on

| Rule                                     | Purpose                           |
| ---------------------------------------- | --------------------------------- |
| `project-context.mdc`                    | Stack + where to edit             |
| `ai-usage.mdc`                           | Session hygiene                   |
| `documentation-maintenance.mdc`          | Docs sync                         |
| `ui-minimal-copy.mdc` / `human-copy.mdc` | Copy policy                       |
| `no-prod-deploy.mdc`                     | Prod guard (unlock: **deskwave**) |
| `phi-data-safety.mdc`                    | PHI/PII                           |
| `audit-logging.mdc`                      | `activity_log` on mutations       |
| `route-guides.mdc`                       | Per-route docs                    |
| `superpowers-opt-in.mdc`                 | Superpowers opt-in                |
| `git-commits.mdc`                        | No AI attribution                 |
| `markitdown-mcp.mdc`                     | PDF/Office via MCP                |

## Glob-scoped

`appointment-workflow.mdc`, `ai-assistant-safety.mdc`, `fastapi-conventions.mdc`, `tanstack-start-conventions.mdc`, `migrations.mdc`, `naming-conventions.mdc`, `mobile-responsive.mdc`, `components.mdc`, `motion.mdc`, `anti-slop-design.mdc`, `security.mdc`, `plan-mode.mdc`, `workflow-docs.mdc`, `self-review.mdc`.

Skills: `.agent/skills/` (symlinked). Commands: `/dd-help`. Subagents: `debugger`, `security-auditor`, `test-runner`, `verifier`, `design-reviewer`. OpenCode: `.opencode/README.md`.
