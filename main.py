"""Context Bridge API.

Run from the backend folder:
    python3 -m uvicorn app.main:app --reload
Interactive docs: http://127.0.0.1:8000/docs
"""
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import APIRouter, FastAPI, HTTPException  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from . import db, llm  # noqa: E402
from .formatting import fit  # noqa: E402
from .schemas import ExtractRequest, HandoffRequest, HandoffResult, Packet, PacketIn  # noqa: E402

app = FastAPI(title="Context Bridge API")
api = APIRouter(prefix="/api")

SEED = PacketIn(
    title="Cross-Tool AI Context Bridge",
    source="Claude",
    goal="Build an app that turns a project's state into a portable context packet that can be pasted into Claude, ChatGPT or Gemini.",
    status="Proposal approved. Synopsis, architecture diagrams and the build plan are next. Editor, formatting and the FastAPI backend are working.",
    decisions=["Packets are structured fields, not raw chat logs",
               "One packet is the source of truth; each AI tool gets its own formatted copy",
               "FastAPI backend with SQLite storage"],
    constraints=["Mini project for the AIAS course", "Must work with tools that have no API, so copy and paste comes first"],
    facts=["Target tools: Claude, ChatGPT, Gemini", "A token is roughly four characters of English"],
    open=["How should packets be versioned when two tools edit the same project?",
          "How can a long transcript be trimmed without losing decisions?"],
    style="Short, practical answers.",
)


@app.on_event("startup")
def startup() -> None:
    db.init()
    if db.count() == 0:
        db.create(SEED)


@api.get("/health")
def health():
    return {"ok": True, "llm_configured": llm.configured(), "model": llm.MODEL}


@api.get("/packets", response_model=List[Packet])
def list_packets():
    return db.list_packets()


@api.post("/packets", response_model=Packet)
def create_packet(p: PacketIn):
    return db.create(p)


@api.get("/packets/{pid}", response_model=Packet)
def get_packet(pid: str):
    p = db.get(pid)
    if not p:
        raise HTTPException(404, "Packet not found")
    return p


@api.put("/packets/{pid}", response_model=Packet)
def update_packet(pid: str, p: PacketIn):
    out = db.update(pid, p)
    if not out:
        raise HTTPException(404, "Packet not found")
    return out


@api.delete("/packets/{pid}")
def delete_packet(pid: str):
    if not db.delete(pid):
        raise HTTPException(404, "Packet not found")
    return {"deleted": pid}


@api.post("/extract", response_model=PacketIn)
def extract(req: ExtractRequest):
    """LLM reads a pasted chat and returns packet fields. Nothing is saved here."""
    return PacketIn(**llm.extract_packet(req.transcript, req.source))


@api.post("/handoff", response_model=HandoffResult)
def handoff(req: HandoffRequest):
    """Format a packet (saved or not) for a target tool. condense=true lets the LLM shorten a long transcript."""
    return fit(req.packet, req.updated, req.target, req.limit_tokens, llm.condense if req.condense else None)


app.include_router(api)

# Serve the built React app (frontend/dist) at "/" when it exists.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/", StaticFiles(directory=str(DIST), html=True), name="web")
