"""Run the support agent on the 20 cases, twice each, and send every run to the platform.

    evalctl run eval.py

Model replies come from recordings/replies.json, so the run is free and the same every time.
A prompt or tool change needs new recordings first: python record.py.
"""

from pathlib import Path

from agent_eval import Eval

from replay import ReplayGemini
from support_agent.agent import CONFIG, LABEL, SupportAgent

HERE = Path(__file__).parent
CASES = HERE / "cases.jsonl"
RECORDINGS = HERE / "recordings" / "replies.json"
# The shop's refund policy as rules, so a regression is caught the same way on every run.
SCORERS = [
    {"key": "run_completed", "check": "run_completed"},
    {"key": "valid_tool_arguments", "check": "valid_tool_arguments"},
    {
        "key": "refund_after_lookup",
        "check": "tool_order",
        "params": {"tool": "issue_refund", "after": ["get_order"]},
    },
    {
        "key": "refund_after_return_check",
        "check": "tool_order",
        "params": {"tool": "issue_refund", "after": ["get_return"]},
    },
    {
        "key": "refund_amount",
        "check": "matches_expected",
        "params": {"field": "refund", "tool": "issue_refund", "argument": "amount"},
    },
]


def main() -> None:
    Eval(
        agent="support-agent",
        task=SupportAgent(ReplayGemini(RECORDINGS)).handle,
        dataset=CASES,
        config=CONFIG,
        repetitions=2,
        label=LABEL,
        scorers=SCORERS,
    )


if __name__ == "__main__":
    main()
