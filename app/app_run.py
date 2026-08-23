"""Step 6 — FastAPI wrapper around the agent.

- POST /chat: {"session_id": str, "message": str} -> {"reply": str, "interrupted": bool, "interrupt_data": ...}
- POST /resume: {"session_id": str, "approved": bool} -> resumes a paused refund
- GET /  : serves the chat UI (static/index.html)

Each session_id becomes the LangGraph thread_id, so conversations on
different sessions never see each other's history.
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from langgraph.types import Command

from app.agent import agent

app = FastAPI(title="Support Agent")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ResumeRequest(BaseModel):
    session_id: str
    approved: bool


def _thread_config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _extract_reply(result: dict):
    """Handle both a normal reply and a paused (interrupted) refund request."""
    interrupted = result.get("__interrupt__")
    if interrupted:
        # interrupted is a list of Interrupt objects; take the first payload
        payload = interrupted[0].value
        return {
            "reply": payload.get("message", "This action needs your approval."),
            "interrupted": True,
            "interrupt_data": payload,
        }
    return {
        "reply": result["messages"][-1].content,
        "interrupted": False,
        "interrupt_data": None,
    }


@app.get("/")
def index():
    return FileResponse("app/static/index.html")


@app.post("/chat")
def chat(req: ChatRequest):
    result = agent.invoke(
        {"messages": [{"role": "user", "content": req.message}]},
        _thread_config(req.session_id),
    )
    return _extract_reply(result)


@app.post("/resume")
def resume(req: ResumeRequest):
    """Called when the UI's approve/reject buttons are clicked after a pause."""
    result = agent.invoke(
        Command(resume={"approved": req.approved}),
        _thread_config(req.session_id),
    )
    return _extract_reply(result)
