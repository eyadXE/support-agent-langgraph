
Week 3 · Task: Build a Real Support Agent
Two tracks: build the whole agent in code, then build it again in n8n. Both are required.
There's no walkthrough and no skeleton to fill in. You get a specification: what the agent must do, the edge cases it must survive, and how you'll prove it. You write all of the code, using the Session 1 and Session 2 decks as your reference. The box below carries the few things that aren't worth guessing — exact imports, the model names, the human-approval shape, and the live API. Everything past it is yours to build.
You'll build the same support agent twice: once in code (Track A) and once no-code in n8n (Track B). Same capabilities, two toolsets — the point is to feel where each approach is faster and where it fights you. Both tracks are required, and each ends in a working agent you can demonstrate.
The reference box and fixture data below are shared by both tracks. If you can't explain why a line of code is there or what a node does, it isn't done — that's the rule for the whole program.
Reference — the bits worth not guessing
Copy these as-is. Everything else you write yourself.
 
# Imports (exact paths -- don't guess these)
from langchain.agents import create_agent
from langchain_core.tools import tool, create_retriever_tool
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.types import Command
 
# Models:   chat = "gemini-3.1-flash-lite"      embeddings = "gemini-embedding-001"
 
# Call the agent  (an agent with a checkpointer REQUIRES a thread_id):
#   cfg = {"configurable": {"thread_id": "some-id"}}
#   out = agent.invoke({"messages": [{"role": "user", "content": "..."}]}, config=cfg)
#   answer = out["messages"][-1].content
 
# Human approval -- detect the pause, then resume:
#   if out.get("__interrupt__"):
#       req = out["__interrupt__"][0].value["action_requests"][0]   # req["name"], req["args"]
#       out = agent.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config=cfg)
#       #                                                  ...or {"type": "reject"}
 
# Live inventory API (no key needed):
#   GET https://dummyjson.com/products/search?q=<item>
#     -> {"products": [ {"title": ..., "price": ..., "stock": ...}, ... ]}   (may be empty)
#   Fake a slow server by appending  &delay=<ms>   (caps at 5000 ms)
 
# Inspect what the agent DID (for evaluation):
#   an AIMessage in out["messages"] has .tool_calls -- a list of {"name": ..., "args": ...}
 

Fixture data — use exactly this
So everyone tests against the same thing, use this order and help-doc data verbatim. (Real stock comes from the live API in Step 4, so no inventory dict here.)
 
ORDERS = {
    "A1234": {"status": "shipped", "eta": "Tuesday", "item": "blue hoodie"},
    "B5678": {"status": "processing", "eta": "not shipped", "item": "red mug"},
}
HELP_DOCS = [
    "Returns: items can be returned within 30 days of delivery for a full refund, if unworn with tags attached.",
    "Refunds go to the original payment method and take 5-7 business days after we receive the returned item.",
    "Shipping: standard is 3-5 business days; express is 1-2 days ($12).",
]
 

Track A · Code
Step 1 · The agent — tools and the loop
Build a support agent with two tools: one that looks up an order from ORDERS, and one that checks stock for an item. Write a system prompt that makes it use its tools instead of guessing, and assemble it with create_agent. You do not write a loop.
Requirements.  The lookup tool must give a clear, distinct message for an order ID that doesn't exist. The stock tool (mock for now — return any sensible number) must give a clear, distinct message for an item the store doesn't sell. “Unknown order” and “unknown item” must not read the same, and neither may crash.
Checkpoint A.  For “is the item from order A1234 in stock?” the agent calls the lookup tool, reads the item, then the stock tool, and only then answers. Ask about order Z9999 and about an item you don't carry — you get two different, sensible replies, no traceback.
Step 2 · Give it knowledge (RAG)
Ground the agent in the HELP_DOCS above. Embed them into a vector store and give the agent a retrieval tool it can call to answer policy questions. Then rebuild the agent so it has all three tools.
Requirements.  A returns question must be answered from the docs, not invented. A policy question the docs do not cover (e.g. gift wrapping) must make the agent say it doesn't know rather than make something up. Prove both.
Checkpoint B.  “Can I return a hoodie I bought two weeks ago?” is answered using the 30-day rule from your docs. “Do you gift-wrap?” gets an honest “I don't have that information,” not a fabricated policy.
Step 3 · Guard the refund (human approval)
Add a process_refund tool that moves money, and make the agent unable to run it without a human's approval. Implement the pause, then the human decision, then the resume — using the human-approval shape from the reference box. The agent needs a checkpointer to pause.
Requirements.  Both outcomes must work and must differ. On approve, the refund completes and the customer is told it's done. On reject, the agent must NOT tell the customer a refund happened — it backs off and offers another path. Demonstrate approve and reject from the same request.
Checkpoint C.  A refund request pauses instead of running, showing the tool and arguments it wants. Approving completes and confirms it; rejecting produces a reply that clearly does not promise the money back.
Step 4 · Connect a real tool (live API)
Replace the mock stock tool with a real call to the DummyJSON product API in the reference box. Same job — item in, stock out — but the number now comes over HTTP from a service you don't own.
Requirements.  The API returns many matching products, each with dozens of fields. Decide which single product's stock you treat as the answer, and be ready to justify that choice. Handle “no matches” as a distinct, clear result — not a crash, not a confusing zero.
Checkpoint D.  “How many iPhones are in stock?” returns a real title, price, and stock from the API. A nonsense query (“widgetzzz”) returns your clean “no such item” result. Print one raw response once to see what you chose to ignore.
Step 5 · Guard the real call
That API can be slow, broken, or empty, and right now a hang takes the whole agent down. Make the tool survive it: a tight timeout, and graceful, distinct results the agent can relay for each failure mode.
Requirements.  Three outcomes must be told apart and each return a clear signal the agent can act on: (1) the call times out, (2) the server returns an error status, and (3) the call succeeds but the item genuinely isn't found. Prove the timeout using the &delay trick from the reference (mind the 5000 ms cap — set your timeout below it). Also cap the reasoning loop so a runaway agent stops instead of spinning.
Checkpoint E.  With a delay forced past your timeout, the agent doesn't freeze — it reports it couldn't check. A forced error status is handled differently from “item not found.” The customer always gets a coherent answer.
Step 6 · Wrap it in an app, and prove it works
Two parts. First, wrap the agent in a FastAPI endpoint with per-user sessions (each request's session becomes the thread_id, so conversations stay separate). Second, write an automated evaluation suite — not eyeballing, measuring.
App.  A POST endpoint that takes a message and a session id and returns the reply. Two messages on the same session stay in context; a new session starts fresh. Prove it with two calls.
Eval.  At least five cases, run automatically, each asserting the RIGHT behaviour — including which tools were or weren't used, not just a word in the answer. Must include: an inventory case that hits the live API, a refund case that must pause, and a case the agent must refuse. Report pass/fail per case, and on failure print the answer and the tools the agent actually called.
Checkpoint F.  The endpoint answers and holds a session. The eval prints a pass/fail line per case; the refund case is caught as “paused,” the refuse case is caught as “declined,” and failures show the tools called so you can see why.
Step 7 · Extension (required) — go past the sessions
Nothing here was walked through in the sessions. Pick ONE and build it. This is where a strong agent separates from a working one.
Option A — LLM-as-judge eval.  Your Step 6 eval matches keywords, which is crude. Replace it (for at least three cases) with a judge: send the question and the agent's answer back to the model and ask it to rule correct or incorrect, with a reason. Parse the verdict and fold it into your pass/fail. Session 1 mentioned this rung existed; you're building it.
Option B — design your own guarded tool.  Invent a second money-touching action (e.g. cancel an order, apply a discount, change a shipping address). Add it with its own human-approval guard and its own edge cases, and add eval cases that prove it pauses and that reject is handled cleanly.
Checkpoint G.  Your chosen extension runs and is covered by at least one eval case. For Option A, a wrong answer that your keyword check passed is now correctly caught by the judge. For Option B, the new tool pauses for approval and rejects cleanly.
Track B · No-Code (n8n)
Now build the same agent with no code, in n8n. Same capabilities, wired as nodes on a canvas. The AI Agent node (choose the Tools agent type) is the brain; you attach sub-nodes for the model, memory, and each tool. The reference box's model names, DummyJSON URL, and fixture data all still apply. n8n's guards and evaluation are coarser than code — that gap is part of what you're here to feel, so note where it helps and where it gets in the way.
n8n 1 · The agent on a canvas
Add a Chat Trigger, then an AI Agent node (Tools agent) connected to it. Attach a Google Gemini Chat Model sub-node (gemini-3.1-flash-lite) and a memory sub-node (Simple / Window Buffer Memory) for sessions, and give it the same system prompt. Add two tools — lookup_order and a mock check_inventory — as Code tools or small sub-workflows that read the fixture ORDERS.
Match Track A.  Unknown order and unknown item must still give different, sensible replies — not the same generic error.
Checkpoint N1.  Open the chat panel, ask “is the item from order A1234 in stock?” and watch the agent call both tools before answering. Unknown order vs unknown item read differently.
n8n 2 · Knowledge (RAG)
Add a Vector Store node (the in-memory / simple one) loaded with the HELP_DOCS via a Google Gemini embeddings node (gemini-embedding-001), and attach it to the AI Agent as a tool. The agent queries it when a question needs the docs.
Checkpoint N2.  A returns question is answered from the docs; a question the docs don't cover makes the agent say it doesn't know, not invent.
n8n 3 · Guard the refund (human approval)
Add a process_refund tool (a sub-workflow or HTTP Request tool). On the connector between the AI Agent and that tool, click the “+” and choose Add human review step, routed to n8n Chat. When the agent tries to refund, execution pauses until you approve or reject.
Match Track A.  Approve must complete and confirm; reject must produce a reply that does not promise the money back. Show both.
Checkpoint N3.  A refund request pauses for your approval instead of running. Approve completes it; reject backs off cleanly.
n8n 4 · Real tool (live API)
Replace the mock stock tool with an HTTP Request tool calling the DummyJSON URL from the reference box. Map title, price, and stock out of the response, and decide which matched product you trust. Handle “no matches” as a distinct result.
Checkpoint N4.  “How many iPhones are in stock?” returns real data from the API; a nonsense query returns your clean “no such item” result.
n8n 5 · Guard the real call
In the HTTP Request node, set a timeout, and turn on Continue On Fail (or wire the node's error output) so a slow or broken call returns a graceful result the agent can relay instead of crashing the run. Tell timeout, error status, and “not found” apart. Force a slow response with the &delay trick to prove it.
Checkpoint N5.  With a forced delay past your timeout, the run doesn't hang — the agent reports it couldn't check. A broken call is handled differently from “item not found.”
n8n 6 · The app, and check it
App.  While building, the Chat Trigger is your app. For “production,” swap it for a Webhook trigger with a Respond to Webhook node; the memory session key keeps each caller's conversation separate. Prove one session stays in context.
Check it.  n8n has no code test suite, so run your Track A test questions through the workflow and read the execution log — it shows the agent's answer and exactly which tools fired. Confirm the refund case pauses and the “should-refuse” case is declined. (Noticing that this is more manual than the code eval is part of the point.)
Checkpoint N6.  The workflow answers over a webhook and holds a session; running your test questions, the execution log shows the right tools firing, the refund pausing, and the refuse case declined.
n8n 7 · Extension (required)
Pick ONE, mirroring Track A's spirit but built with nodes:
Option A — a judge node.  Add a second LLM (a Basic LLM Chain node) that takes the question and the agent's answer and rules correct or incorrect with a reason — an LLM judge, wired visually.
Option B — a second guarded tool.  Add another money-touching tool (cancel order, apply discount) with its own Add human review step and its own edge handling.
Checkpoint N7.  Your chosen extension runs and is visible in an execution — the judge scores an answer, or the new tool pauses for approval and rejects cleanly.
Done when
Ship it.  BOTH tracks work. Each agent — the code one and the n8n one — answers order, live-stock, and policy questions; distinguishes unknown-order, unknown-item, API-failure, and out-of-stock; pauses for refund approval and handles reject cleanly; runs behind an endpoint or webhook with sessions; is checked against your test questions; and includes its Step 7 extension. If you can walk a reviewer through any line of code and the role of any node, and say why each is there, you're done.
