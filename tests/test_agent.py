from typing import Any

from replay import Candidate, Content, FunctionCall, Part, Reply, UsageMetadata
from support_agent.agent import SupportAgent, escalate, get_order, get_return, issue_refund


def _reply(text: str | None = None, *calls: tuple[str, dict[str, Any]]) -> Reply:
    parts = [Part(text=text)] if text else []
    parts += [Part(function_call=FunctionCall(name, args)) for name, args in calls]
    return Reply([Candidate(Content(parts))], UsageMetadata(100, 10))


class Scripted:
    """Plays the model with a fixed list of replies and keeps what it was asked."""

    def __init__(self, *replies: Reply) -> None:
        self.replies = list(replies)
        self.asked: list[Any] = []
        self.models = self

    def generate_content(self, *, model: str, contents: Any, config: Any = None) -> Reply:
        self.asked.append(list(contents))
        return self.replies.pop(0)


def test_the_shop_tools_follow_the_policy_data() -> None:
    assert get_order("ord_2004")["total"] == 102.0
    assert get_order("ord_2002")["refunded"] == 45.0
    assert get_return("ord_2004") == {"order_id": "ord_2004", "arrived": ["socks"], "value": 12.0}
    assert get_return("ord_2003")["arrived"] == []
    assert issue_refund("ord_2006", 10)["error"] == "order ord_2006 cannot be refunded"
    assert "error" in issue_refund("ord_2001", 500)
    assert escalate("app crash")["ticket"] == "esc_none"


def test_the_graph_runs_tools_until_the_model_replies() -> None:
    model = Scripted(
        _reply(None, ("get_order", {"order_id": "ord_2001"})),
        _reply(None, ("get_return", {"order_id": "ord_2001"})),
        _reply(None, ("issue_refund", {"order_id": "ord_2001", "amount": 59.0})),
        _reply("I have refunded 59.00 for the headphones."),
    )
    out = SupportAgent(model).handle({"message": "Refund ord_2001 please."})
    assert out == {"reply": "I have refunded 59.00 for the headphones."}
    # The last question carried every tool result back to the model.
    names = [
        p["function_response"]["name"]
        for t in model.asked[-1]
        if isinstance(t, dict)
        for p in t["parts"]
        if "function_response" in p
    ]
    assert names == ["get_order", "get_return", "issue_refund"]


def test_the_graph_stops_after_its_turn_limit() -> None:
    looping = Scripted(*[_reply(None, ("get_order", {"order_id": "ord_2001"}))] * 3)
    out = SupportAgent(looping, max_turns=2).handle({"message": "?"})
    assert out == {"reply": "Sorry, I could not finish this request."}
