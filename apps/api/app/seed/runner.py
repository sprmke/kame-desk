"""Populate local Postgres with synthetic clinic data for UI/UX review."""

from __future__ import annotations

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.seed.clear import clear_demo_data, demo_data_exists
from app.seed.constants import (
    ADMIN_EMAIL,
    CLINIC_NAME,
    CLINIC_SLUG,
    DEMO_PASSWORD,
    ORG_NAME,
    OWNER_EMAIL,
    PLATFORM_EMAIL,
    RECEPTION_EMAIL,
)
from app.seed.populate import SeedResult, seed_demo_data
from app.services.embedding_service import upsert_soap_note_embedding


def print_seed_summary(result: SeedResult) -> None:
    print("")
    print("Demo data seeded successfully.")
    print("")
    print(f"  Clinic: {CLINIC_NAME} (/{CLINIC_SLUG})")
    print(f"  Organization: {ORG_NAME} (platform billing only)")
    print(f"  Password for all staff accounts: {DEMO_PASSWORD}")
    print("")
    print("  Solo clinic accounts")
    print(f"    owner       {OWNER_EMAIL}  (also the clinic doctor)")
    print(f"    reception   {RECEPTION_EMAIL}")
    print(f"    admin       {ADMIN_EMAIL}")
    print(f"    platform    {PLATFORM_EMAIL}  (also Super Admin when allow-listed)")
    print("")
    print("  Public booking: /book/" + CLINIC_SLUG)
    print("")
    platform_ok = PLATFORM_EMAIL in settings.platform_admin_email_list
    if platform_ok:
        print(f"  Super Admin: {PLATFORM_EMAIL} can open /platform")
    else:
        print("  Super Admin: add this to apps/api/.env, then restart the API:")
        print(f"    PLATFORM_ADMIN_EMAILS={PLATFORM_EMAIL}")
    print("")
    print("  Log in at /login, then open /dashboard.")
    print("")


async def _embed_soap_notes(note_ids: list) -> None:
    if not note_ids:
        return
    async with AsyncSessionLocal() as embed_db:
        for note_id in note_ids[:16]:
            await upsert_soap_note_embedding(embed_db, note_id)


async def run_seed(force: bool = False) -> None:
    async with AsyncSessionLocal() as db:
        exists = await demo_data_exists(db)
        if exists and not force:
            print(f"Demo data already exists ({CLINIC_SLUG}).")
            print("Run: pnpm run db:reset:local")
            print("Or:  pnpm run db:seed:force")
            return
        if exists and force:
            await clear_demo_data(db)
        result = await seed_demo_data(db)
    await _embed_soap_notes(result.soap_note_ids)
    print_seed_summary(result)
