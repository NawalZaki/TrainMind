"""Gemini-backed text generation for TrainMind.

Embeddings remain local in Ollama; only text generation uses Gemini.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-3.8-flash"


def get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


@lru_cache(maxsize=1)
def _get_client(api_key: str):
    return genai.Client(api_key=api_key)



def generate_text(prompt: str, *, json_mode: bool = False) -> str:
    """Generate text with Gemini and retry temporary server errors."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add your Gemini API key to the project's .env file."
        )

    config_options = {
        "temperature": 0.2,
        "max_output_tokens": int(
            os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "12000")
        ),
    }

    if json_mode:
        config_options["response_mime_type"] = "application/json"

    client = _get_client(api_key)
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=get_model_name(),
                contents=prompt,
                config=types.GenerateContentConfig(**config_options),
            )
            break

        except Exception as exc:
            message = str(exc)
            lowered = message.lower()

            if (
                "429" in message
                or "quota" in lowered
                or "resource_exhausted" in lowered
            ):
                raise RuntimeError(
                    "Gemini Free Tier quota or rate limit was reached. "
                    "Wait and try again, or check your Google AI Studio quota. "
                    "No Ollama generation fallback is enabled."
                ) from exc

            if (
                "api key" in lowered
                or "unauthenticated" in lowered
                or "permission" in lowered
            ):
                raise RuntimeError(
                    "Gemini rejected the API key. "
                    "Check GEMINI_API_KEY in your .env file."
                ) from exc

            temporary_error = any(
                code in message
                for code in ("503", "500", "502", "504")
            )

            if temporary_error and attempt < max_attempts - 1:
                wait_seconds = 2 ** (attempt + 1)
                print(
                    f"Temporary Gemini server error. "
                    f"Retrying in {wait_seconds} seconds "
                    f"(attempt {attempt + 2}/{max_attempts})..."
                )
                time.sleep(wait_seconds)
                continue

            raise RuntimeError(
                f"Gemini generation failed: {message}"
            ) from exc

    text = getattr(response, "text", None)

    if not text or not text.strip():
        raise RuntimeError(
            "Gemini returned an empty response. Try a shorter topic "
            "or check the model's availability."
        )

    return text.strip()


def generate_answer(question: str, context: str) -> str:
    """Answer using only retrieved curriculum context."""
    prompt = f"""You are TrainMind, an AI assistant for ITI trainers.

Answer the user's request using ONLY the supplied curriculum context.
If the context does not contain enough information, say so clearly.
Do not add facts, tools, prerequisites, or procedures from outside the context.
Keep the answer clear and useful, and cite source/page information when present.

CURRICULUM CONTEXT:
{context}

USER REQUEST:
{question}
"""
    return generate_text(prompt)


def generate_json(prompt: str) -> str:
    """Generate a JSON response for structured package generation."""
    return generate_text(prompt, json_mode=True)
