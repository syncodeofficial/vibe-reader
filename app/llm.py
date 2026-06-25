"""The part that does the magic: turn a pile of chat into structured insight.

This talks to OpenRouter, which is OpenAI-compatible — so we use the openai SDK
and just point it at OpenRouter's base URL. That lets us pick from hundreds of
models (including free ones) by changing a single string.
"""

import json
import os

from openai import OpenAI

from .models import ReadRequest, ReadResponse

# Which model to use, in OpenRouter's "provider/model" format.
# Free models end in ":free". Swap this any time without touching code.
# Browse options at https://openrouter.ai/models
MODEL = os.environ.get("VIBE_MODEL", "google/gemini-2.0-flash-exp:free")

# The system prompt sets the role and, crucially, pins the output contract.
# Being strict about "JSON only, no prose, no code fences" is what makes the
# response parseable every time.
SYSTEM_PROMPT = """You read live-stream chat the way a sharp co-host would: you \
catch the real questions buried in the noise, feel the mood of the room, and \
know the one thing the streamer should do next to ride the energy.

You always reply with a single JSON object and nothing else. No prose before or \
after, no markdown, no code fences. The object must match exactly this shape:

{
  "vibe": {"word": "<one lowercase word for the mood>", "read": "<one sentence>"},
  "questions": [
    {"asker": "<username>", "question": "<the question, cleaned up>",
     "why_it_lands": "<one line on why it's worth answering>"}
  ],
  "topics": [{"label": "<short topic>", "heat": <integer 1-5>}],
  "the_move": "<one punchy line the streamer could say or do next>"
}

Rules:
- Pick at most 4 questions, best first. A question can be implied, not just \
literal ("can you show the config?" counts). Skip spam and one-word noise.
- If nobody really asked anything, return an empty questions list. Don't invent.
- At most 5 topics, hottest first. Heat reflects how much the chat circles it.
- Keep "the_move" specific to what's actually happening in the chat."""


def _build_user_message(req: ReadRequest) -> str:
    """Flatten the request into the text we hand the model."""
    topic_line = (
        f"The stream is about: {req.stream_topic}\n\n" if req.stream_topic else ""
    )
    chat_lines = "\n".join(f"{m.author}: {m.text}" for m in req.messages)
    return f"{topic_line}Here is the recent chat:\n\n{chat_lines}"


def _strip_to_json(raw: str) -> str:
    """Be forgiving: if the model wraps JSON in fences anyway, dig it out."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # drop the opening fence (``` or ```json) and the closing fence
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.rsplit("```", 1)[0]
    return cleaned.strip()


def read_the_room(req: ReadRequest) -> ReadResponse:
    """Send the chat to the model via OpenRouter and parse the reply.

    Raises RuntimeError with a readable message if the key is missing or the
    model returns something we can't parse, so the API layer can turn that into
    a clean HTTP error instead of a stack trace.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        # Optional headers: these just label your traffic in the OpenRouter
        # dashboard at https://openrouter.ai/activity so you can see usage.
        default_headers={
            "HTTP-Referer": "https://syncode.ie",
            "X-Title": "Vibe Reader",
        },
    )

    completion = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(req)},
        ],
    )

    raw_text = completion.choices[0].message.content or ""
    try:
        data = json.loads(_strip_to_json(raw_text))
        return ReadResponse(**data)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuntimeError(f"Could not parse the model's reply as JSON: {exc}") from exc
