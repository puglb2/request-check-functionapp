import os
import requests
from typing import Any, Dict, Optional

# Works for OpenAI-style chat completions endpoints commonly used in Azure/OpenAI gateways.
# If your endpoint differs, you only change this file.

OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT", "").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "")
OPENAI_DEPLOYMENT = os.getenv("OPENAI_DEPLOYMENT", "")  # Azure deployment name (if applicable)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5-chat")

class OpenAIError(Exception):
    pass

def _build_url() -> str:
    # Prefer Azure deployment route if OPENAI_DEPLOYMENT is set.
    if OPENAI_DEPLOYMENT:
        # Example: https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions?api-version=...
        if not OPENAI_API_VERSION:
            raise OpenAIError("OPENAI_API_VERSION is required when using Azure deployment route.")
        return f"{OPENAI_ENDPOINT}/openai/deployments/{OPENAI_DEPLOYMENT}/chat/completions?api-version={OPENAI_API_VERSION}"

    # Otherwise assume OpenAI-compatible base url for chat completions.
    # Example: https://api.openai.com/v1/chat/completions or a gateway that supports it.
    return f"{OPENAI_ENDPOINT}/v1/chat/completions"

def chat_json(system: str, user: str, schema_hint: Optional[Dict[str, Any]] = None, temperature: float = 0.1) -> Dict[str, Any]:
    url = _build_url()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "api-key": OPENAI_API_KEY  # keeps Azure-compatible gateways happy
    }

    payload: Dict[str, Any] = {
        "model": MODEL_NAME if not OPENAI_DEPLOYMENT else None,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": temperature
    }

    # Remove model if Azure deployment route (it’s implied)
    if OPENAI_DEPLOYMENT:
        payload.pop("model", None)

    # Lightweight “hint” (optional). Real strict JSON enforcement depends on your endpoint support.
    if schema_hint:
        payload["response_format"] = {"type": "json_object"}

    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code >= 400:
        raise OpenAIError(f"OpenAI call failed {r.status_code}: {r.text[:800]}")

    return r.json()
