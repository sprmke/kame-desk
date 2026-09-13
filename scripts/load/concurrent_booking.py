#!/usr/bin/env python3
"""Concurrent booking load probe against a running local API.

Usage:
  DOCTORDESK_TESTING=1 uv run python scripts/load/concurrent_booking.py \\
    --base-url http://localhost:8100 \\
    --token <access_token> \\
    --clinic-id <uuid> \\
    --doctor-id <uuid> \\
    --patient-id <uuid> \\
    --workers 20

Expect exactly one 200 and the rest 409 when all workers target the same slot.
"""

from __future__ import annotations

import argparse
import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import httpx


async def _book(
    client: httpx.AsyncClient,
    *,
    headers: dict[str, str],
    doctor_id: str,
    patient_id: str,
    start: datetime,
    end: datetime,
) -> int:
    res = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
        },
    )
    return res.status_code


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8100")
    parser.add_argument("--token", required=True)
    parser.add_argument("--clinic-id", required=True)
    parser.add_argument("--doctor-id", required=True)
    parser.add_argument("--patient-id", required=True)
    parser.add_argument("--workers", type=int, default=20)
    args = parser.parse_args()

    headers = {
        "Authorization": f"Bearer {args.token}",
        "X-Clinic-Id": args.clinic_id,
    }
    start = datetime(2027, 3, 15, 2, 0, tzinfo=UTC)
    end = start + timedelta(minutes=30)

    async with httpx.AsyncClient(base_url=args.base_url, timeout=30.0) as client:
        results = await asyncio.gather(
            *[
                _book(
                    client,
                    headers=headers,
                    doctor_id=args.doctor_id,
                    patient_id=args.patient_id,
                    start=start,
                    end=end,
                )
                for _ in range(args.workers)
            ]
        )

    ok = sum(1 for code in results if code == 200)
    conflict = sum(1 for code in results if code == 409)
    other = [code for code in results if code not in (200, 409)]
    print(f"workers={args.workers} ok={ok} conflict={conflict} other={other}")
    if ok != 1 or conflict != args.workers - 1:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
