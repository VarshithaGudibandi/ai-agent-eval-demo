"""Record Gemini's replies once, then replay them, so the eval gate gives the same answer on
every run and costs nothing.

Record mode passes each call to a real google-genai client and saves its reply. Replay mode
answers from the saved replies and never touches the network: a call it has no reply for
fails, so a changed prompt or tool forces a new recording instead of a silent guess."""

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class MissingReplyError(LookupError):
    """The call was never recorded. Record again with the real model."""


def _get(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _part(part: Any) -> dict[str, Any]:
    call, result = _get(part, "function_call"), _get(part, "function_response")
    found: dict[str, Any] = {}
    if _get(part, "text"):
        found["text"] = _get(part, "text")
    if call is not None:
        found["call"] = {"name": _get(call, "name"), "args": dict(_get(call, "args") or {})}
    if result is not None:
        found["result"] = {"name": _get(result, "name"), "response": _get(result, "response")}
    return found


def _conversation(contents: Any) -> list[dict[str, Any]]:
    """The conversation as plain data, the same whether it holds google-genai objects, dicts
    or this module's replies, so a recorded run and its replay ask the same question."""
    return [
        {"role": _get(turn, "role"), "parts": [_part(p) for p in _get(turn, "parts") or []]}
        for turn in contents
    ]


def request_key(model: str, contents: Any, config: Any) -> str:
    system = _get(config, "system_instruction") if config is not None else None
    tools = _get(config, "tools") if config is not None else None
    document = {
        "model": model,
        "system": system,
        "tools": tools,
        "contents": _conversation(contents),
    }
    return hashlib.sha256(json.dumps(document, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class FunctionCall:
    name: str
    args: dict[str, Any]


@dataclass
class Part:
    text: str | None = None
    function_call: FunctionCall | None = None


@dataclass
class Content:
    parts: list[Part]
    role: str = "model"


@dataclass
class Candidate:
    content: Content


@dataclass
class UsageMetadata:
    prompt_token_count: int
    candidates_token_count: int
    cached_content_token_count: int | None = None
    thoughts_token_count: int | None = None


@dataclass
class Reply:
    candidates: list[Candidate]
    usage_metadata: UsageMetadata | None = None


def _save(response: Any) -> dict[str, Any]:
    content = _get(_get(response, "candidates")[0], "content")
    usage = _get(response, "usage_metadata")
    return {
        "parts": [_part(p) for p in _get(content, "parts") or []],
        "usage": {
            "prompt_token_count": _get(usage, "prompt_token_count") or 0,
            "candidates_token_count": _get(usage, "candidates_token_count") or 0,
            "cached_content_token_count": _get(usage, "cached_content_token_count"),
            "thoughts_token_count": _get(usage, "thoughts_token_count"),
        },
    }


def _load(saved: dict[str, Any]) -> Reply:
    parts = [
        Part(
            text=p.get("text"),
            function_call=FunctionCall(p["call"]["name"], p["call"]["args"])
            if "call" in p
            else None,
        )
        for p in saved["parts"]
    ]
    return Reply([Candidate(Content(parts))], UsageMetadata(**saved["usage"]))


@dataclass
class Models:
    path: Path
    live: Any
    replies: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    seen: Counter[str] = field(default_factory=Counter)

    def generate_content(self, *, model: str, contents: Any, config: Any = None) -> Any:
        key = request_key(model, contents, config)
        # The same question can come up more than once, as in repeated runs of a case; each
        # occurrence keeps its own reply.
        n = self.seen[key]
        self.seen[key] += 1
        recorded = self.replies.get(key, [])
        if n < len(recorded):
            return _load(recorded[n])
        if self.live is None:
            raise MissingReplyError(
                f"no recorded reply for request {key[:12]} (occurrence {n + 1})"
            )
        response = self.live.models.generate_content(model=model, contents=contents, config=config)
        self.replies.setdefault(key, []).append(_save(response))
        self.path.write_text(json.dumps(self.replies, indent=1, sort_keys=True) + "\n")
        return response


class ReplayGemini:
    """A stand-in for google-genai's client. Give it a live client to record."""

    def __init__(self, path: Path, live: Any = None) -> None:
        replies = json.loads(path.read_text()) if path.exists() else {}
        self.models = Models(path, live, replies)
