from typing import Any

DEFAULT_NOTIFICATION_PREFERENCES: dict[str, Any] = {
    "email_enabled": True,
    "sms_enabled": False,
    "whatsapp_enabled": False,
    "confirmation_enabled": True,
    "reminder_24h_enabled": True,
    "reminder_2h_enabled": False,
    "sender_name": None,
    "chronic_condition_rules": [],
}


def merged_preferences(clinic_prefs: dict[str, Any] | None) -> dict[str, Any]:
    merged = {**DEFAULT_NOTIFICATION_PREFERENCES, **(clinic_prefs or {})}
    if merged.get("chronic_condition_rules") is None:
        merged["chronic_condition_rules"] = []
    return merged
