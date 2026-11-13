# AI Agent Eval demo

A small support agent for an online shop, evaluated by [AI Agent Eval](https://github.com/VarshithaGudibandi/ai-agent-eval).

The agent is a LangGraph graph with two steps: a model step that calls Gemini, and a tool step that looks up orders, checks returns, refunds and escalates. The shop's policy is in its prompt: look the order up and check the return before any refund, refund only what came back, never refund twice, and escalate damage, app and payment problems.

`replay.py` records the model's replies once and replays them, so runs cost nothing and give the same answer every time.

## Run the tests

```bash
uv sync
uv run pytest
```
