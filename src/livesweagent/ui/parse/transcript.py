"""Transcript parsing utilities for the opencode-style UI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


TranscriptItemType = Literal[
    "user_input",
    "assistant_output",
    "assistant_reasoning",
    "tool_call",
    "tool_output",
    "system",
]


@dataclass(frozen=True)
class TranscriptItem:
    type: TranscriptItemType
    text: str


_BASH_BLOCK_RE = re.compile(r"```bash\s*\n(.*?)\n```", re.DOTALL)


def parse_assistant_message(content: str) -> list[TranscriptItem]:
    """Split assistant content into reasoning/command/output segments.

    Expected format (from bundled YAML configs):

    - A THOUGHT section before the command
    - Exactly one ```bash ...``` block

    If the message is malformed, returns a single assistant_output item.
    """

    matches = list(_BASH_BLOCK_RE.finditer(content))
    if len(matches) != 1:
        return [TranscriptItem("assistant_output", content.strip())]

    match = matches[0]
    prefix = content[: match.start()].strip()
    bash = match.group(1).strip()
    suffix = content[match.end() :].strip()

    items: list[TranscriptItem] = []
    if prefix:
        if "THOUGHT:" in prefix:
            items.append(TranscriptItem("assistant_reasoning", prefix))
        else:
            items.append(TranscriptItem("assistant_output", prefix))

    if bash:
        items.append(TranscriptItem("tool_call", bash))

    if suffix:
        items.append(TranscriptItem("assistant_output", suffix))

    return items


def is_tool_output(text: str) -> bool:
    stripped = text.lstrip()
    if stripped.startswith("Observation:"):
        return True
    if stripped.startswith("<returncode>"):
        return True
    if "<output>" in text and "</output>" in text:
        return True
    if "<warning>" in text and "</warning>" in text:
        return True
    return False


def messages_to_transcript(messages: list[dict]) -> list[TranscriptItem]:
    """Convert DefaultAgent messages -> transcript entries.

    Note: DefaultAgent uses role='user' for both real user text and for tool
    observations/errors; we use a small heuristic to classify them.
    """

    transcript: list[TranscriptItem] = []
    first_user_seen = False

    for message in messages:
        role = message.get("role")
        content = message.get("content")

        if isinstance(content, list):
            content_str = "\n".join([str(item.get("text", "")) for item in content])
        else:
            content_str = str(content)

        if role == "system":
            continue

        if role == "assistant":
            transcript.extend(parse_assistant_message(content_str))
            continue

        if role == "user":
            if not first_user_seen:
                first_user_seen = True
                transcript.append(TranscriptItem("user_input", content_str.strip()))
            elif is_tool_output(content_str):
                transcript.append(TranscriptItem("tool_output", content_str.strip()))
            else:
                transcript.append(TranscriptItem("system", content_str.strip()))
            continue

        transcript.append(TranscriptItem("system", content_str.strip()))

    return transcript
