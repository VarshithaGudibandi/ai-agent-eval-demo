"""Record the real model's replies for every case, twice each, into recordings/replies.json.

    GEMINI_API_KEY=... python record.py

Replies already recorded are reused, so only new questions reach the model. Calls are paced
to stay under the free tier's per-minute limit; a failed conversation is undone and run again
in full, because Gemini accepts only its own earlier turns back."""

import copy
import json
import sys
import time
from collections import Counter
from typing import Any

from google import genai

from eval import CASES, RECORDINGS
from replay import ReplayGemini
from support_agent.agent import SupportAgent

REPETITIONS = 2


class Paced:
    """The live client, with a pause before each call."""

    def __init__(self, client: Any, pause: float = 1.5) -> None:
        self.client, self.pause, self.models = client, pause, self

    def generate_content(self, **kwargs: Any) -> Any:
        time.sleep(self.pause)
        return self.client.models.generate_content(**kwargs)


def main() -> None:
    gemini = ReplayGemini(RECORDINGS, Paced(genai.Client()))
    agent = SupportAgent(gemini)
    cases = [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]
    for case in cases:
        for rep in range(1, REPETITIONS + 1):
            for _attempt in range(8):
                seen = Counter(gemini.models.seen)
                replies = copy.deepcopy(gemini.models.replies)
                try:
                    reply = agent.handle(case["input"])["reply"]
                    print(f"{case['key']} #{rep}: {reply[:90]}")
                    break
                except Exception as exc:
                    gemini.models.seen, gemini.models.replies = seen, replies
                    RECORDINGS.write_text(json.dumps(replies, indent=1, sort_keys=True) + "\n")
                    wait = 60 if "429" in str(exc) else 10
                    print(f"{case['key']} #{rep}: {type(exc).__name__}, retrying in {wait} s")
                    time.sleep(wait)
            else:
                sys.exit(f"gave up on {case['key']}")


if __name__ == "__main__":
    main()
