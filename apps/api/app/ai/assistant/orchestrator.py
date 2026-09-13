import json
import re
from dataclasses import dataclass
from typing import Any

from app.ai.assistant.context import AttachedContextItem, PageContext, ResolvedContext
from app.ai.assistant.safety import assert_tool_registered


@dataclass
class ParsedToolCall:
    name: str
    args: dict[str, Any]


_TOOL_PREFIX = "__tool__:"
_TOOLS_PREFIX = "__tools__:"


def build_resolved_context(
    page: PageContext | None,
    attached: list[AttachedContextItem],
) -> ResolvedContext:
    return ResolvedContext(page=page or PageContext(), attached=attached)


def parse_tool_calls(content: str) -> list[ParsedToolCall]:
    text = content.strip()
    if text.startswith(_TOOLS_PREFIX):
        payload = json.loads(text[len(_TOOLS_PREFIX) :])
        return [ParsedToolCall(name=item["name"], args=item.get("args") or {}) for item in payload]

    if text.startswith(_TOOL_PREFIX):
        payload = json.loads(text[len(_TOOL_PREFIX) :])
        return [ParsedToolCall(name=payload["name"], args=payload.get("args") or {})]

    match = re.search(r"__tool__:(\{.*\})", text)
    if match:
        payload = json.loads(match.group(1))
        return [ParsedToolCall(name=payload["name"], args=payload.get("args") or {})]

    return []


def summarize_tool_result(tool_name: str, result: dict[str, Any]) -> str:
    if tool_name == "search_patients":
        names = [i.get("full_name", "") for i in result.get("items", [])]
        return f"Found {result.get('total', 0)} patients: {', '.join(names) or 'none'}."
    if tool_name == "check_patient_balance":
        return (
            f"Balance: {result.get('balance')} ({result.get('open_invoice_count')} open invoices)."
        )
    if tool_name == "get_patient":
        return f"Patient: {result.get('full_name')} (#{result.get('patient_number')})."
    return f"{tool_name} completed."


def validate_tool_name(name: str) -> None:
    assert_tool_registered(name)
