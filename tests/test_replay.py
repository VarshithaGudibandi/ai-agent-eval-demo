from pathlib import Path
from typing import Any

import pytest

from replay import MissingReplyError, ReplayGemini, request_key
from tests.test_agent import Scripted, _reply

CONFIG = {"system_instruction": "Be careful.", "tools": [{"function_declarations": []}]}
QUESTION = [{"role": "user", "parts": [{"text": "Where is ord_2006?"}]}]


def test_a_recording_is_replayed_without_the_live_model(tmp_path: Path) -> None:
    path = tmp_path / "replies.json"
    live = Scripted(_reply("first"), _reply("second"))
    recorder = ReplayGemini(path, live)
    answers = [
        recorder.models.generate_content(model="m", contents=QUESTION, config=CONFIG)
        for _ in range(2)
    ]
    assert [a.candidates[0].content.parts[0].text for a in answers] == ["first", "second"]
    replayer = ReplayGemini(path)
    again = [
        replayer.models.generate_content(model="m", contents=QUESTION, config=CONFIG)
        for _ in range(2)
    ]
    # Each repetition of the same question gets its own recorded reply, in order.
    assert [a.candidates[0].content.parts[0].text for a in again] == ["first", "second"]
    assert again[0].usage_metadata.prompt_token_count == 100
    with pytest.raises(MissingReplyError):
        replayer.models.generate_content(model="m", contents=QUESTION, config=CONFIG)


def test_a_changed_prompt_is_a_new_question(tmp_path: Path) -> None:
    path = tmp_path / "replies.json"
    ReplayGemini(path, Scripted(_reply("ok"))).models.generate_content(
        model="m", contents=QUESTION, config=CONFIG
    )
    changed = {**CONFIG, "system_instruction": "Be quick."}
    with pytest.raises(MissingReplyError):
        ReplayGemini(path).models.generate_content(model="m", contents=QUESTION, config=changed)


def test_the_key_is_the_same_for_real_objects_and_their_replay() -> None:
    model_turn: Any = _reply(None, ("get_order", {"order_id": "ord_2006"})).candidates[0].content
    as_dict = {
        "role": "model",
        "parts": [{"function_call": {"name": "get_order", "args": {"order_id": "ord_2006"}}}],
    }
    assert request_key("m", [*QUESTION, model_turn], CONFIG) == request_key(
        "m", [*QUESTION, as_dict], CONFIG
    )
