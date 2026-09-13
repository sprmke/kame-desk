import hashlib
import math
import os

from app.core.config import settings


def _use_stub_embeddings() -> bool:
    if os.environ.get("DOCTORDESK_TESTING") == "1":
        return True
    return not settings.openai_api_key.strip()


def _stub_embedding(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    dim = settings.embedding_dimensions
    values: list[float] = []
    for i in range(dim):
        byte = digest[i % len(digest)]
        values.append((byte / 127.5) - 1.0)
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


async def embed_text(text: str) -> tuple[list[float], str]:
    cleaned = text.strip()
    if not cleaned:
        cleaned = "empty"

    if _use_stub_embeddings():
        return _stub_embedding(cleaned), settings.embedding_model_version

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=cleaned,
            dimensions=settings.embedding_dimensions,
        )
        vector = response.data[0].embedding
        return vector, settings.openai_embedding_model
    except ImportError:
        return _stub_embedding(cleaned), settings.embedding_model_version


def soap_note_embedding_text(
    subjective: str | None,
    objective: str | None,
    assessment: str | None,
    plan: str | None,
    diagnosis_primary: str | None,
) -> str:
    parts = [
        subjective or "",
        objective or "",
        assessment or "",
        plan or "",
        diagnosis_primary or "",
    ]
    return "\n".join(p for p in parts if p.strip())
