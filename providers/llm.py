"""
LLM provider — works with ANY OpenAI-compatible endpoint.

Groq, Ollama, OpenAI, together.ai, etc. are all drop-in via .env — no code
changes, just swap LLM_BASE_URL / LLM_API_KEY / LLM_MODEL. This is the
only place in the pipeline that talks to the LLM; every worker imports
`chat` or `chat_json`.

If FALLBACK_LLM_BASE_URL is set, a failed primary call (down, rate-limited,
out of credits) automatically retries once against the fallback — meant for
a local Ollama model so the pipeline never fully stalls on a Groq outage.

pip install openai python-dotenv
"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)
_MODEL = os.environ["LLM_MODEL"]

_FALLBACK_BASE_URL = os.environ.get("FALLBACK_LLM_BASE_URL")
_FALLBACK_MODEL = os.environ.get("FALLBACK_LLM_MODEL")
_fallback_client = (
    OpenAI(base_url=_FALLBACK_BASE_URL, api_key=os.environ.get("FALLBACK_LLM_API_KEY", "ollama"))
    if _FALLBACK_BASE_URL
    else None
)


def chat(messages, **kwargs) -> str:
    """messages: standard OpenAI-style [{"role": ..., "content": ...}, ...]"""
    try:
        resp = _client.chat.completions.create(model=_MODEL, messages=messages, **kwargs)
        return resp.choices[0].message.content
    except Exception as primary_error:
        if _fallback_client is None:
            raise
        print(
            f"[llm] primary ({_MODEL}) failed: {primary_error!r} — "
            f"falling back to {_FALLBACK_MODEL}",
            file=sys.stderr,
        )
        resp = _fallback_client.chat.completions.create(
            model=_FALLBACK_MODEL, messages=messages, **kwargs
        )
        return resp.choices[0].message.content


def chat_json(messages, **kwargs) -> str:
    """Same as chat(), but asks the provider to return a JSON object.
    Supported by Groq and recent Ollama builds — use for extraction,
    ranking, and critic steps where you want structured output back."""
    return chat(messages, response_format={"type": "json_object"}, **kwargs)
