# E-Commerce Support Agent — LangGraph · RAG · Human-in-the-Loop

A production-shaped customer support agent: it looks up real order/stock data instead of guessing, answers policy questions only from grounded documents, and refuses to move money without a human clicking approve. Built in two tracks — **Track A** fully in code (LangChain/LangGraph), **Track B** the same capability set rebuilt no-code in n8n (`docs/n8n-workflow-track-b.json`) — to make visible where no-code is faster and where it isn't.

## 1 · The business problem

An online store's support team drowns in three kinds of tickets:

- **"Where is my order?" / "Do you have this in stock?"** — high volume, zero judgment needed, but only if the system can *look up* real data instead of guessing.
- **Policy questions** ("can I return these shoes?") — answerable from the store's own docs, yet LLMs confidently invent policies when asked something the docs don't cover ("do you gift-wrap?"). A made-up policy creates a promise the business has to keep.
- **Money-touching actions** (refunds) — exactly where automation pays off most and goes wrong worst. No unattended system should be able to move money, and a customer must never be told a refund happened when it didn't.

On top of that: any agent calling a third-party API inherits its failure modes. A slow inventory server can freeze an otherwise perfect assistant.

## 2 · How this project solves it

- **Answers from tools, not imagination.** Order lookup and stock checks are tool calls with distinct, non-crashing handling for unknown orders vs unknown items. The system prompt forbids guessing; the eval suite verifies which tools actually fired.
- **Grounded policy answers via RAG.** The help docs are embedded locally (free `all-MiniLM-L6-v2`, no data leaves the machine) into a vector store exposed as a retrieval tool. Uncovered topics get an honest "I don't have that information" instead of a fabricated policy.
- **Refunds require a human.** `process_refund` triggers a **LangGraph interrupt**: the run pauses showing exactly what it wants to do, a human approves or rejects, and the graph resumes. On rejection the agent backs off without ever claiming money moved — verified by direct testing of both the approve and reject paths.
- **Survives a broken world.** The live DummyJSON inventory call has a tight timeout and returns three distinct signals — timeout / HTTP error / not found — each relayed coherently to the customer instead of a generic failure.
- **Measured, not eyeballed.** An automated eval suite asserts behavior including which tools fired; the extension replaces keyword matching with an **LLM-as-judge** that rules replies correct/incorrect against explicit criteria — catching substantively wrong answers that contain the right words.
- **Same agent, no code.** Track B rebuilds identical capabilities as an n8n workflow — a real comparison of where no-code wins (wiring speed) and where it fights you (guardrails, evaluation).

## 3 · Tech & architecture

```
                        ┌────────────────────────────────────┐
user ──► FastAPI ──►    │  LangGraph agent (checkpointer)    │
        /chat,/resume   │   ├─ get_order_status (fixture)    │
        session =       │   ├─ get_stock_status (live API,   │
        thread_id       │   │    timeout + error modes)      │
        per user        │   ├─ search_policy_docs (RAG,      │
                        │   │    local embeddings)           │
                        │   └─ process_refund ──► INTERRUPT  │
                        │        human approves/rejects      │
                        └────────────────────────────────────┘
                                   ▼
                     evals/: case runner asserting tools fired,
                     refund-pause caught, refusals declined,
                     LLM-as-judge for reply quality
```

```
app/
├── agent.py          # Single agent definition: 4 tools + system prompt + checkpointer
├── config.py         # Model setup (OpenRouter, temperature 0)
├── app_run.py        # FastAPI wrapper: /chat, /resume, static chat UI
├── vectorstore.py    # Embeddings built once per process
├── data/             # Fixture orders, stock, help docs
├── tools/            # orders · stock (guarded live API) · retrieval · refund (interrupt)
└── evals/            # cases · helpers · judge (LLM-as-judge) · run_eval
```

**Key engineering decisions**

- One agent definition (`agent.py`) shared by the app *and* the evals — one source of truth, so eval results reflect exactly what's deployed.
- Embeddings run locally on purpose: free, private, and fast enough for a handful of short docs; the retrieval tool returns an explicit `NO_RELEVANT_INFO` signal so the model can decline honestly rather than pad an answer.
- Each HTTP session maps to a LangGraph `thread_id`, so conversations never bleed into each other.
- Automatic tool-calling is used here deliberately (unlike this author's `banking-assistant`, where it's hand-written) — the tradeoff between framework convenience and hand-rolled control-flow visibility is a real design decision, made per-project rather than by default.

## Skills Demonstrated

- **Agentic state-machine design with a real human-in-the-loop gate.** `process_refund` uses a genuine LangGraph `interrupt()`, not a UI-only confirmation dialog — the graph execution itself pauses and resumes, which is the pattern production agentic systems need for any irreversible action.
- **Designing for graceful, distinguishable failure.** The stock-check tool separates timeout, HTTP error, and not-found into three different signals relayed differently to the customer, instead of collapsing every failure into one generic error message.
- **Grounding over guessing.** RAG retrieval returns an explicit sentinel (`NO_RELEVANT_INFO`) rather than an empty result, so the system prompt can force an honest "I don't know" — a small design choice that prevents a common and costly LLM failure mode.
- **Eval-driven development beyond keyword matching.** Built an LLM-as-judge evaluation layer on top of a simpler assertion-based suite, specifically to catch replies that contain the right words but are substantively wrong.
- **Real debugging on integration boundaries, not just prompt tweaking.** Traced and fixed a demo that silently always failed because its mock order referenced a product that didn't exist in the live third-party API it was tested against, and a RAG relevance threshold tuned tighter than real on-topic queries actually scored — the kind of bug that only surfaces by testing against live behavior, not by re-reading the prompt.
- **Honest evaluation reporting.** The eval suite currently passes 5 of 7 cases; the 2 known failures are documented with root causes (one is third-party API fuzzy-search behavior outside this codebase's control, the other is a documented prompt-injection limitation where the human-approval gate still blocks the refund from ever completing even if the agent is talked into attempting the call) rather than hidden or silently skipped.
- **No-code/code capability parity as a deliberate comparison**, not just a checkbox — Track B surfaces concretely where n8n is faster to build and where its guardrails and evaluation story is weaker than hand-written code.

## Screenshots

*(Screenshots coming soon)*

## Running it

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
# add a real OPENROUTER_API_KEY to .env (free tier at openrouter.ai/keys)
.venv\Scripts\python -m uvicorn app.app_run:app --port 8000
```

Open `http://127.0.0.1:8000/` for the chat UI. Full setup, a scripted demo walkthrough, and the known eval limitations are in [`HOW_TO_RUN.md`](HOW_TO_RUN.md).

Docker:

```bash
docker build -t support-agent .
docker run -p 8000:8000 -e OPENROUTER_API_KEY=sk-or-... support-agent
```

Deployable as-is to Railway / Render / Fly.io (respects `$PORT`); set the key as a secret.
