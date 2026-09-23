from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.data.public_intake import normalize_intake_fields, require_public_intake


def test_normalize_intake_defaults_off():
    fields = normalize_intake_fields(None)
    assert fields["email"] is False
    assert fields["notes"] is False


def test_require_email_when_enabled():
    fields = normalize_intake_fields({"email": True})
    data = SimpleNamespace(
        email=None,
        birthdate=None,
        sex=None,
        address=None,
        reason_for_visit=None,
        is_existing_patient=None,
    )
    with pytest.raises(HTTPException) as exc:
        require_public_intake(fields, data)
    assert exc.value.status_code == 400
