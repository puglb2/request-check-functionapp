import azure.functions as func
import json
from shared.logging_utils import get_request_id
from shared.openai_client import chat_json

def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)

    raw = chat_json(
        system="You are a JSON engine. Return {\"ok\": true}.",
        user="Return JSON only.",
        schema_hint={"type": "object"},
        temperature=0
    )

    content = raw["choices"][0]["message"]["content"]

    resp = func.HttpResponse(
        content,
        mimetype="application/json",
        status_code=200
    )
    resp.headers["x-request-id"] = rid
    return resp
