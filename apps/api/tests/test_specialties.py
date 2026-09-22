import pytest
from fastapi import HTTPException

from app.data.specialties import resolve_specialty, soap_template_for_specialty_key


def test_legacy_general_practice_maps_to_gp():
    key, other, label = resolve_specialty(specialty="General Practice")
    assert key == "general_practitioner"
    assert other is None
    assert label == "General practitioner"


def test_other_requires_text():
    with pytest.raises(HTTPException) as exc:
        resolve_specialty(specialty_key="other")
    assert exc.value.status_code == 400


def test_soap_template_mapping():
    assert soap_template_for_specialty_key("dentist") == "dental"
    assert soap_template_for_specialty_key("obgyn") == "obgyn"
    assert soap_template_for_specialty_key("cardiologist") == "general"
    assert soap_template_for_specialty_key(None) == "general"
