"""Step 6 (automated eval) + Step 7 Option A (LLM judge), combined.

Run with:  python -m app.evals.run_eval
"""
import uuid

from app.agent import agent
from app.evals.cases import EVAL_CASES
from app.evals.helpers import get_called_tools, get_reply_text, was_interrupted
from app.evals.judge import judge_reply


def run_case(case: dict) -> dict:
    """Runs one case on a fresh thread and returns a result dict."""
    thread_id = f"eval-{case['id']}-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    result = agent.invoke(
        {"messages": [{"role": "user", "content": case["message"]}]},
        config,
    )

    called_tools = get_called_tools(result)
    interrupted = was_interrupted(result)
    reply = get_reply_text(result)

    # --- Behavioural checks that apply to every case, regardless of `check` ---
    tools_ok = case["expected_tools"].issubset(called_tools) if case["expected_tools"] else True
    interrupt_ok = interrupted == case["expect_interrupt"]

    reasons = []
    if not tools_ok:
        reasons.append(
            f"expected tools {case['expected_tools']} not fully in called tools {called_tools}"
        )
    if not interrupt_ok:
        reasons.append(
            f"expected interrupt={case['expect_interrupt']} but got interrupt={interrupted}"
        )

    # --- Content check, per case type ---
    if case["check"] == "tools_only":
        content_ok = True  # already covered by tools_ok / interrupt_ok above

    elif case["check"] == "keyword":
        low = reply.lower()
        content_ok = any(kw.lower() in low for kw in case["must_contain"])
        if not content_ok:
            reasons.append(f"reply did not contain any of {case['must_contain']}")

    elif case["check"] == "judge":
        if interrupted:
            # Can't judge text that doesn't exist yet (refund cases pause).
            content_ok = True
        else:
            verdict = judge_reply(case["message"], reply, case["criteria"])
            content_ok = verdict["verdict"] == "pass"
            if not content_ok:
                reasons.append(f"judge: {verdict['reason']}")
    else:
        raise ValueError(f"Unknown check type: {case['check']}")

    passed = tools_ok and interrupt_ok and content_ok

    return {
        "id": case["id"],
        "passed": passed,
        "reasons": reasons,
        "reply": reply,
        "called_tools": called_tools,
        "interrupted": interrupted,
    }


def main():
    results = [run_case(case) for case in EVAL_CASES]

    print("\n=== EVAL RESULTS ===")
    n_pass = 0
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        if r["passed"]:
            n_pass += 1
        print(f"[{status}] {r['id']}")
        if not r["passed"]:
            print(f"    reasons: {r['reasons']}")
            print(f"    reply: {r['reply']!r}")
            print(f"    tools called: {r['called_tools']}")
            print(f"    interrupted: {r['interrupted']}")

    print(f"\n{n_pass}/{len(results)} passed")


if __name__ == "__main__":
    main()
