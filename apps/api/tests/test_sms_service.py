from app.services.sms_service import normalize_ph_e164


def test_normalize_ph_mobile_local():
    assert normalize_ph_e164("09171234567") == "+639171234567"


def test_normalize_ph_already_e164():
    assert normalize_ph_e164("+639171234567") == "+639171234567"


def test_normalize_ph_without_zero():
    assert normalize_ph_e164("9171234567") == "+639171234567"
