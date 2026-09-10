"""
LLM provider — works with ANY OpenAI-compatible endpoint.

Groq, Ollama, OpenAI, together.ai, etc. are all drop-in via .env — no code
changes, just swap LLM_BASE_URL / LLM_API_KEY / LLM_MODEL. This is the
only place in the pipeline that talks to the LLM; every worker imports
`chat` or `chat_json`.

pip install openai python-dotenv
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)
_MODEL = os.environ["LLM_MODEL"]


def chat(messages, **kwargs) -> str:
    """messages: standard OpenAI-style [{"role": ..., "content": ...}, ...]"""
    resp = _client.chat.completions.create(model=_MODEL, messages=messages, **kwargs)
    return resp.choices[0].message.content


def chat_json(messages, **kwargs) -> str:
    """Same as chat(), but asks the provider to return a JSON object.
    Supported by Groq and recent Ollama builds — use for extraction,
    ranking, and critic steps where you want structured output back."""
    return chat(messages, response_format={"type": "json_object"}, **kwargs)
