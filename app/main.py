"""Vibe Reader — a tiny FastAPI service that reads live-stream chat.

Run it with:  uvicorn app.main:app --reload
Then open:    http://127.0.0.1:8000

The interactive API docs are at http://127.0.0.1:8000/docs
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .llm import read_the_room
from .models import ReadRequest, ReadResponse

app = FastAPI(
    title="Vibe Reader",
    description="Reads a batch of live-stream chat and hands back the mood, "
    "the questions worth answering, the hot topics, and the next move.",
    version="1.0.0",
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    """Cheap check that the server is up (useful for deploys and uptime pings)."""
    return {"status": "ok"}


@app.post("/read", response_model=ReadResponse)
def read(req: ReadRequest) -> ReadResponse:
    """Read the room. Takes chat in, returns structured insight out."""
    try:
        return read_the_room(req)
    except RuntimeError as exc:
        # Turn our readable internal errors into a clean 502 for the frontend.
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/")
def home() -> FileResponse:
    """Serve the demo page so the whole thing runs from one command."""
    return FileResponse(STATIC_DIR / "index.html")
