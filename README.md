# E-Commerce Support Agent — LangGraph · RAG · Human-in-the-Loop

Built during the **Exology Pioneer Program (Week 3)** in two required tracks: **Track A** fully in code (LangChain/LangGraph), **Track B** no-code (n8n — `docs/n8n-workflow-track-b.json`).

## 1 · The business problem

An online store's support team drowns in three kinds of tickets:

- **"Where is my order?" / "Do you have this in stock?"** — high volume, zero judgment needed, but only if the system can *look up* real data instead of guessing.
- **Policy questions** ("can I return these shoes?") — answerable from the store's own docs, yet LLMs confidently invent policies when asked something the docs don't cover ("do you gift-wrap?"). A made-up policy creates a promise the business has to keep.
- **Money-touching actions** (refunds) — exactly where automation pays off most and goes wrong worst. No unattended system should be able to move money, and a customer must never be told a refund happened when it didn't.

On top of that: any agent calling a third-party API inherits its failure modes. A slow inventory server can freeze an otherwise perfect assistant.

## 2 · How this project solves it

- **Answers from tools, not imagination.** Order lookup and stock checks are tool calls with distinct, non-crashing handling for unknown orders vs unknown items. The system prompt forbids guessing; the eval suite verifies which tools actually fired.
- **Grounded policy answers via RAG.** The help docs are embedded locally (free `all-MiniLM-L6-v2`, no data leaves the machine) into a vector store exposed as a retrieval tool. Uncovered topics get an honest "I don't have that information."
- **Refunds require a human.** `process_refund` triggers a **LangGraph interrupt**: the run pauses showing exactly what it wants to do, a human approves or rejects, and the graph resumes. On rejection the agent backs off without promising money back — verified by an eval case.
- **Survives a broken world.** The live DummyJSON inventory call has a tight timeout (< the forced-delay cap) and returns three distinct signals — timeout / HTTP error / not found — each relayed coherently to the customer.
- **Measured, not eyeballed.** An automated eval suite asserts behavior including tool usage; the extension replaces keyword matching with an **LLM-as-judge** that rules replies correct/incorrect against explicit criteria — catching substantively wrong answers that contain the right words.
- **Same agent, no code.** Track B rebuilds identical capabilities as an n8n workflow — making visible where no-code is faster (wiring) and where it fights you (guards, evaluation).

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

- One agent definition (`agent.py`) shared by the app *and* the evals — one source of truth.
- Embeddings run locally on purpose: free, private, and fast enough for 3 short docs; the retrieval tool returns an explicit `NO_RELEVANT_INFO` signal so the model can decline honestly.
- Each HTTP session maps to a LangGraph `thread_id`, so conversations never bleed into each other.

## Run it

Local (Python 3.10+, needs `OPENROUTER_API_KEY` in `.env`; ~80 MB embedding model downloads once):

```bash
pip install -r requirements.txt && cp .env.example .env   # add your key
uvicorn app.app_run:app --reload       # web app + API → http://127.0.0.1:8000
python -m app.evals.run_eval           # automated eval suite
# or: ./run.sh {api|eval}
```

Try in the UI:

1. *"Is the item from order A1234 in stock?"* → chains order lookup → stock check
2. *"Can I return a hoodie I bought two weeks ago?"* → answered from RAG docs (30-day rule)
3. *"Do you gift-wrap?"* → honest "I don't have that information"
4. *"I want a refund for order A1234"* → pauses for approval; rejecting backs off cleanly

Docker:

```bash
docker build -t support-agent .
docker run -p 8000:8000 -e OPENROUTER_API_KEY=sk-or-... support-agent
```

Deployable as-is to Railway / Render / Fly.io (respects `$PORT`); set the key as a secret.

## Skills demonstrated

Agentic workflow design (LangGraph state machines) · tool calling · RAG with local embeddings · human-in-the-loop interrupts for money-touching actions · graceful degradation of third-party APIs · session management · eval-driven development (process vs outcome) · LLM-as-judge evaluation · no-code replication (n8n).
