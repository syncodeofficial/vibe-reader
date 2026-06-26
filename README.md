# Vibe Reader

A tiny **FastAPI + OpenRouter** service that reads a slice of live-stream chat
and hands back four things a streamer actually wants mid-broadcast:

- **the room's vibe** — one word + a one-line read
- **the questions worth answering** — the real ones, pulled out of the noise
- **what the room keeps circling** — topic clusters with a heat rating
- **the move** — one specific thing to say or do next

It talks to any model on [OpenRouter](https://openrouter.ai) (free or paid)
through one OpenAI-compatible call, and ships with a small console-style demo
page so the whole thing runs from one command. Built as a FastAPI prototype of
a feature that fits LiveQ.

---

## Run it

You need Python 3.10+ and an OpenRouter API key (free models work with $0 balance).

```bash
# 1. install
pip install -r requirements.txt

# 2. add your key
cp .env.example .env        # then edit .env and paste your key
```

Then set the key in your shell and run:

```bash
# macOS / Linux
export OPENROUTER_API_KEY=sk-or-...

# Windows PowerShell
$env:OPENROUTER_API_KEY = "sk-or-..."
```

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** for the demo, or
**http://127.0.0.1:8000/docs** for the auto-generated API docs.

---

## The API

`POST /read`

```json
{
  "stream_topic": "Building a SaaS live with Next.js",
  "messages": [
    { "author": "dev_marta", "text": "can you show the supabase RLS policy again?" },
    { "author": "sam_builds", "text": "vercel or fly for deploy?" }
  ]
}
```

Returns:

```json
{
  "vibe": { "word": "curious", "read": "The room is engaged and asking real build questions." },
  "questions": [
    { "asker": "dev_marta", "question": "Can you show the Supabase RLS policy again?",
      "why_it_lands": "Multiple people are stuck on the same thing — high payoff to clarify." }
  ],
  "topics": [{ "label": "Supabase RLS", "heat": 4 }],
  "the_move": "Re-share the RLS policy on screen and explain it line by line."
}
```

---

## Choosing a model

The model is set with the `VIBE_MODEL` environment variable, in OpenRouter's
`provider/model` format. Free models end in `:free`. Browse them at
[openrouter.ai/models](https://openrouter.ai/models).

```bash
# Windows PowerShell example
$env:VIBE_MODEL = "openrouter/free"
```

Prefer an instruction-following model here — the app depends on the model
returning clean JSON, so reasoning models that emit their thinking can break
parsing.

---

## How it's built

| File | Job |
|------|-----|
| `app/models.py` | Pydantic models — validate the request, lock the response shape |
| `app/llm.py` | Prompt engineering + the OpenRouter call; parses JSON back into types |
| `app/main.py` | FastAPI routes, error handling, serves the demo |
| `static/index.html` | The console demo UI |

The interesting part is `llm.py`: the system prompt pins an exact JSON contract
so the model behaves like a typed function, not a chatbot. Everything downstream
treats the model output as structured data.

---

## Talking points

- **Structured output from an LLM.** The whole design turns a language model into
  a typed endpoint by enforcing a JSON contract in the system prompt and parsing
  it back into Pydantic models. That's the pattern behind most "AI feature" work.
- **Provider-agnostic.** Built on OpenRouter's OpenAI-compatible API, so swapping
  models (free or paid, across providers) is a one-line change.
- **Prompt engineering as the product.** The quality lives in the prompt: how it
  decides what counts as a real question, when to return nothing instead of
  inventing, and how heat is judged.
- **It's a real feature, not a toy.** This is a FastAPI cut of something that fits
  LiveQ — reading live chat to surface questions and topics.
- **Graceful failure.** Missing key, bad model output → clean HTTP errors, not
  stack traces. The frontend shows the message instead of breaking.