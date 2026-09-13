"""Deterministic allergy and drug interaction checks (MVP curated list)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DrugReference, PatientMedicalInfo


def _norm(value: str) -> str:
    return value.strip().lower()


async def _load_drug_refs(db: AsyncSession, drug_names: list[str]) -> list[DrugReference]:
    if not drug_names:
        return []
    norms = {_norm(n) for n in drug_names if n.strip()}
    if not norms:
        return []
    result = await db.execute(
        select(DrugReference).where(
            or_(
                func.lower(DrugReference.name).in_(norms),
                func.lower(DrugReference.generic_name).in_(norms),
            )
        )
    )
    return list(result.scalars().all())


async def _patient_allergies(db: AsyncSession, patient_id: uuid.UUID) -> list[dict[str, Any]]:
    result = await db.execute(
        select(PatientMedicalInfo).where(PatientMedicalInfo.patient_id == patient_id)
    )
    info = result.scalar_one_or_none()
    if info is None:
        return []
    return list(info.allergies or [])


async def _patient_medications(db: AsyncSession, patient_id: uuid.UUID) -> list[str]:
    result = await db.execute(
        select(PatientMedicalInfo).where(PatientMedicalInfo.patient_id == patient_id)
    )
    info = result.scalar_one_or_none()
    if info is None:
        return []
    names: list[str] = []
    for med in info.current_medications or []:
        if isinstance(med, dict) and med.get("name"):
            names.append(str(med["name"]))
    return names


def _allergy_matches(drug: DrugReference, allergy: dict[str, Any]) -> str | None:
    substance = _norm(str(allergy.get("substance", "")))
    if not substance:
        return None
    if substance in {_norm(drug.name), _norm(drug.generic_name)}:
        return f"Patient allergy: {allergy.get('substance')}"
    for cls in drug.known_allergen_classes or []:
        if substance == _norm(cls) or substance in _norm(cls):
            return f"Patient allergy to {allergy.get('substance')} ({cls} class)"
        if _norm(cls) in substance or substance in _norm(cls):
            return f"Patient allergy to {allergy.get('substance')} ({cls} class)"
    return None


def _interaction_message(a: DrugReference, b_name: str) -> str | None:
    b = _norm(b_name)
    for target in a.interaction_with or []:
        if _norm(target) == b or b in _norm(target) or _norm(target) in b:
            return f"Interaction between {a.name} and {b_name}"
    return None


async def check_allergy_interaction_conflicts(
    db: AsyncSession,
    patient_id: uuid.UUID,
    drug_names: list[str],
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    refs = await _load_drug_refs(db, drug_names)
    allergies = await _patient_allergies(db, patient_id)
    current_meds = await _patient_medications(db, patient_id)

    for drug in refs:
        for allergy in allergies:
            msg = _allergy_matches(drug, allergy)
            if msg:
                flags.append(
                    {
                        "type": "allergy",
                        "drug_name": drug.name,
                        "message": msg,
                        "related": str(allergy.get("substance", "")),
                    }
                )

    for drug in refs:
        for other in drug_names:
            if _norm(other) == _norm(drug.name):
                continue
            msg = _interaction_message(drug, other)
            if msg:
                flags.append(
                    {
                        "type": "interaction",
                        "drug_name": drug.name,
                        "message": msg,
                        "related": other,
                    }
                )
        for med in current_meds:
            msg = _interaction_message(drug, med)
            if msg:
                flags.append(
                    {
                        "type": "interaction",
                        "drug_name": drug.name,
                        "message": msg,
                        "related": med,
                    }
                )

    # Penicillin allergy vs amoxicillin by class even if drug not in reference exact match
    for name in drug_names:
        n = _norm(name)
        if "amoxicillin" in n or "augmentin" in n:
            for allergy in allergies:
                substance = _norm(str(allergy.get("substance", "")))
                if "penicillin" in substance:
                    flags.append(
                        {
                            "type": "allergy",
                            "drug_name": name,
                            "message": f"Patient allergy: {allergy.get('substance')}",
                            "related": str(allergy.get("substance", "")),
                        }
                    )

    matched = {_norm(r.name) for r in refs} | {_norm(r.generic_name) for r in refs}
    for name in drug_names:
        n = _norm(name)
        covered = n in matched or any(n in m or m in n for m in matched if m)
        if not covered:
            flags.append(
                {
                    "type": "unchecked",
                    "drug_name": name,
                    "message": "Not in the clinic drug list. Interaction was not checked.",
                    "related": None,
                }
            )

    seen = set()
    unique: list[dict[str, str]] = []
    for flag in flags:
        key = (flag["type"], flag["drug_name"], flag["message"])
        if key not in seen:
            seen.add(key)
            unique.append(flag)
    return unique
