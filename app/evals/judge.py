"""Step 7 — Option A: LLM-as-judge.

Replaces crude keyword matching for the cases marked check == "judge".
Sends the question, the agent's reply, and pass criteria back to the
model and asks it to rule correct/incorrect with a reason, so eval cases
can catch answers that use the right words but are substantively wrong —
exactly what a keyword check would miss.
"""
import json

from app.config import model

_JUDGE_SYSTEM_PROMPT = """You are a strict grading judge for a customer
support agent's replies. You will be given:
- the customer's question
- the criteria for what counts as a correct reply
- the agent's actual reply

Decide if the reply satisfies the criteria. Respond with ONLY a JSON
object, no markdown fences, no extra text, in exactly this shape:
{"verdict": "pass" or "fail", "reason": "one sentence explaining why"}
"""


def judge_reply(question: str, reply: str, criteria: str) -> dict:
    """Returns {"verdict": "pass"|"fail", "reason": str}."""
    prompt = (
        f"Question: {question}\n\n"
        f"Criteria for a correct reply: {criteria}\n\n"
        f"Agent's actual reply: {reply}\n\n"
        "Judge now."
    )
    response = model.invoke(
        [
            {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
    )
    raw = response.content.strip()
    # Strip accidental markdown fences in case the model adds them anyway.
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        parsed = json.loads(raw)
        verdict = parsed.get("verdict", "fail").lower()
        reason = parsed.get("reason", "")
    except (json.JSONDecodeError, AttributeError):
        verdict, reason = "fail", f"Judge returned unparseable output: {raw!r}"

    return {"verdict": "pass" if verdict == "pass" else "fail", "reason": reason}
