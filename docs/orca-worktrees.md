# Orca worktrees

Each Orca worktree runs its own web app on a sticky port. The API, worker, and
Docker services on the primary stack are shared.

## Ports

| Checkout             | Port                 |
| -------------------- | -------------------- |
| Primary checkout     | `3100`               |
| Other Orca worktrees | Sticky `3700`-`3799` |

```bash
bun run ui          # this worktree's web app, writes .local/vite-port
bun run ui:port     # print the port only
```

## Orca setup

Repo root [`orca.yaml`](../orca.yaml):

- `scripts.setup` → `pnpm install` + copy `apps/web/.env.development` from `ORCA_ROOT_PATH`
- `defaultTabs` → opens a **UI** tab that runs `bun run ui`
- `scripts.archive` → stops only this worktree's web server

In Orca: **Settings → Projects → kame-desk → Worktree hooks → Advanced →
Command source** → **orca.yaml only**.

Start the shared backend once with `./dev.sh` (Docker services, API on `:8100`,
worker, and the primary web app). A worktree's UI tab starts only the web app
against that shared API.

## Local sign-in

There is no seeded local test user in this repo. Use the account configured for
the local API. OAuth callbacks must be registered for the port you use.

## Verify

1. `./dev.sh` once in the primary checkout.
2. `bun run ui` in the worktree, then open the printed URL.
3. Sign in and confirm the dashboard and patient pages load from the shared API.
