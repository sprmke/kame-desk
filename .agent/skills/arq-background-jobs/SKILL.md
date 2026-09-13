---
name: arq-background-jobs
description: ARQ job conventions, retry/idempotency, worker vs request handler split.
---

# ARQ background jobs

- Definitions in `apps/api/app/workers/`
- Jobs: transcription, embeddings, recurring expand, reminders (later phases).
- **Idempotent** — safe to retry; use dedupe keys where needed.
- Heavy work never blocks HTTP — enqueue from service after commit.
- Same business logic in services, not duplicated in job bodies.
