import azure.functions as func
import json
from shared.logging_utils import Timer, get_request_id, log_json, safe_len
from shared.openai_client import chat_json, OpenAIError

SYSTEM_PROMPT = (
    "You are a compliance extraction engine. "
    "Return ONLY JSON. No prose."
)

def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)
    t_all = Timer()

    try:
        payload = req.get_json()
    except Exception:
        payload = None

    if not isinstance(payload, dict):
        return _resp(400, rid, {"error": "Invalid JSON body", "request_id": rid})

    # Expected fields (we’ll expand later)
    ocr_text = payload.get("ocr_text", "")
    checklist = payload.get("checklist", [])  # later you can keep this server-side for caching
    debug = req.params.get("debug") == "1"

    log_json("hipaa_check.request", {
        "request_id": rid,
        "ocr_chars": safe_len(ocr_text),
        "checklist_items": len(checklist) if isinstance(checklist, list) else None
    })

    # Stub behavior for now: just validate wiring and model call optionally
    # If you pass {"dry_run": true}, it won't call the model (cheap).
    if payload.get("dry_run") is True:
        out = {
            "request_id": rid,
            "ok": True,
            "dry_run": True
        }
        if debug:
            out["timing_ms"] = {"total": t_all.ms()}
        return _resp(200, rid, out)

    # Minimal model call placeholder (you’ll replace with real checklist logic)
    user_prompt = (
        "Extract whether this text looks like it contains ANY HIPAA compliance controls. "
        "Return JSON with keys: {\"has_controls\": boolean, \"notes\": string}.\n\n"
        f"OCR_TEXT:\n{ocr_text[:20000]}"
    )

    t_llm = Timer()
    try:
        raw = chat_json(SYSTEM_PROMPT, user_prompt, schema_hint={"type":"object"}, temperature=0.1)
    except OpenAIError as e:
        log_json("hipaa_check.openai_error", {"request_id": rid, "err": str(e)})
        return _resp(502, rid, {"error": "Model call failed", "request_id": rid})

    # Try to pull content safely (varies by endpoint). We keep debug info either way.
    result = {"request_id": rid, "raw": raw}
    result["timing_ms"] = {"llm": t_llm.ms(), "total": t_all.ms()}

    return _resp(200, rid, result if debug else {"request_id": rid, "ok": True})

def _resp(code: int, rid: str, obj: dict) -> func.HttpResponse:
    resp = func.HttpResponse(
        body=json.dumps(obj, ensure_ascii=False),
        status_code=code,
        mimetype="application/json"
    )
    resp.headers["x-request-id"] = rid
    return resp
