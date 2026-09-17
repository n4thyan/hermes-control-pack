from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import re


def _quoted(text: str) -> list[str]:
    values: list[str] = []
    for match in re.finditer(r'''["'“”‘’]([^"'“”‘’]{1,500})["'“”‘’]''', text):
        value = match.group(1).strip()
        if value:
            values.append(value)
    return values


def _tomorrow_window() -> tuple[str, str]:
    local_now = datetime.now().astimezone()
    tomorrow = (local_now + timedelta(days=1)).date()
    start_local = datetime.combine(tomorrow, datetime.min.time(), tzinfo=local_now.tzinfo)
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        end_local.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )


def _clean_trigger(value: str) -> str:
    text = value.strip(" \t\r\n,.;:!?\"'")
    text = re.sub(r"\s+(?:or whatever|or something|please)$", "", text, flags=re.IGNORECASE).strip()
    return text[:200]


def capture_explicit_future_response(user_message: str) -> dict[str, Any] | None:
    """Parse only narrow, explicit future-response instructions.

    HCP deliberately does not treat arbitrary prose as executable memory. This parser
    recognizes user-authored forms such as "tomorrow when I say X, reply with Y" and
    "when I prompt you X next session, respond with Y". Ambiguous messages return None
    and remain available to the model through normal HCP context/tooling.
    """
    raw = str(user_message or "").strip()
    low = raw.casefold()
    if not raw:
        return None
    future_hint = any(token in low for token in (
        "tomorrow", "next session", "next time", "after i restart", "when i reopen",
        "when i launch hermes", "when i start hermes", "when i wake up",
    ))
    trigger_hint = any(token in low for token in (
        "when i say", "when i prompt", "when i type", "when i ask", "prompt u", "prompt you",
    ))
    response_hint = any(token in low for token in (
        "reply", "respond", "say back", "answer with", "simply say",
    ))
    if not (future_hint and trigger_hint and response_hint):
        return None

    quotes = _quoted(raw)
    action = quotes[-1] if quotes else ""
    if not action:
        action_match = re.search(
            r"(?:reply|respond|answer)\s+(?:to me\s+)?(?:with\s+)?[:\-]?\s*([^,.!?\n]{1,300})$",
            raw,
            flags=re.IGNORECASE,
        )
        if action_match:
            action = action_match.group(1).strip(" \t\"'")
    if not action:
        return None

    trigger = ""
    if len(quotes) >= 2:
        trigger = quotes[-2]
    if not trigger:
        patterns = (
            r"when\s+i\s+(?:say|type|ask)\s+(.+?)(?=\s*(?:,|then\b|tomorrow\b|next\s+session\b|next\s+time\b|i\s+want\b|please\b))",
            r"when\s+i\s+prompt\s+(?:u|you)\s+(.+?)(?=\s*(?:,|then\b|tomorrow\b|next\s+session\b|next\s+time\b|i\s+want\b|please\b))",
            r"prompt\s+(?:u|you)\s+(.+?)(?=\s*(?:,|then\b|tomorrow\b|next\s+session\b|next\s+time\b|i\s+want\b|please\b))",
        )
        for pattern in patterns:
            match = re.search(pattern, raw, flags=re.IGNORECASE)
            if match:
                trigger = _clean_trigger(match.group(1))
                if trigger:
                    break
    if not trigger:
        return None

    payload: dict[str, Any] = {
        "action": action,
        "action_type": "respond_exact",
        "trigger_type": "contains_any",
        "trigger_patterns": [trigger],
        "scope": "global",
        "consume_after_success": True,
        "priority": "important",
        "note": "Automatically captured by HCP from an explicit user-authored future response instruction.",
    }
    if "tomorrow" in low:
        payload["active_after"], payload["expires_at"] = _tomorrow_window()
    return payload
