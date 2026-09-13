---
name: alembic-migrations
description: Alembic autogenerate review, btree_gist exclusion constraints, never edit shipped migrations.
---

# Alembic migrations

- Never edit files already in git under `apps/api/migrations/versions/`.
- Enable `btree_gist` before doctor/room exclusion constraints.
- One logical change per migration when possible.
- Review autogenerate for missing indexes on `clinic_id` FKs.

```bash
pnpm run db:migrate:new
pnpm run db:migrate
```

See `migrations.mdc` and `fix-migration-issues` skill.
