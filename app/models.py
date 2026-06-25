"""Request and response shapes for the Vibe Reader API.

Pydantic models do two jobs here: they validate whatever the frontend sends,
and they document the exact JSON the API promises to return. FastAPI reads
these classes to generate the interactive docs at /docs for free.
"""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single line from the live chat."""

    author: str = Field(..., examples=["nightowl_92"])
    text: str = Field(..., examples=["wait how did you set up the OBS scene??"])


class ReadRequest(BaseModel):
    """What the frontend posts: a batch of chat plus a little context."""

    stream_topic: str = Field(
        default="",
        description="What the stream is about. Helps the model judge relevance.",
        examples=["Building a SaaS live with Next.js"],
    )
    messages: list[ChatMessage] = Field(
        ...,
        min_length=1,
        description="The recent chat messages to read.",
    )


class Question(BaseModel):
    """A question worth answering on stream, with a reason it matters."""

    asker: str
    question: str
    why_it_lands: str = Field(
        ..., description="One line on why answering this is worth the stream's time."
    )


class Topic(BaseModel):
    """A cluster the chat keeps circling back to."""

    label: str
    heat: int = Field(..., ge=1, le=5, description="How hot, 1 (faint) to 5 (on fire).")


class RoomVibe(BaseModel):
    """The overall mood of the room in one word plus a short read."""

    word: str = Field(..., examples=["curious"])
    read: str = Field(..., description="A sentence on where the room's energy is.")


class ReadResponse(BaseModel):
    """Everything the API hands back, ready to drop into a dashboard."""

    vibe: RoomVibe
    questions: list[Question]
    topics: list[Topic]
    the_move: str = Field(
        ..., description="One punchy thing the streamer could say or do next."
    )
