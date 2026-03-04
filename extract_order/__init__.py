import azure.functions as func
import json
import re

from shared.logging_utils import Timer, get_request_id, log_json, safe_len
from shared.openai_client import chat_json, OpenAIError
from shared.docintel import extract_text
from engine.prompts import ORDER_EXTRACT_SYSTEM


def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)
    t_all = Timer()
    debug = req.params.get("debug") == "1"

    if not req.files:
        return _resp(400, rid, {"error": "File required", "request_id": rid})

    f = req.files.get("file")
    if not f:
        return _resp(400, rid, {"error": "File missing", "request_id": rid})

    pdf_bytes = f.read()

    try:
        ocr_text = extract_text(pdf_bytes)
    except Exception as e:
        return _resp(500, rid, {"error": "OCR failed", "details": str(e), "request_id": rid})

    ocr_text = re.sub(r"\r", "", ocr_text)
    ocr_text = re.sub(r"\n+", "\n", ocr_text)
    ocr_text = re.sub(r"[ \t]+", " ", ocr_text)

    log_json("extract_order.request", {"request_id": rid, "ocr_chars": safe_len(ocr_text)})

    t_llm = Timer()
    try:
        raw = chat_json(
            ORDER_EXTRACT_SYSTEM,
            f"DOCUMENT TEXT:\n{ocr_text[:14000]}",
            schema_hint={"type": "object"},
            temperature=0.0
        )
    except OpenAIError as e:
        return _resp(502, rid, {"error": "Model call failed", "details": str(e), "request_id": rid})

    try:
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except Exception:
        return _resp(500, rid, {"error": "Failed to parse model output", "request_id": rid})

    if debug:
        parsed["timing_ms"] = {"llm": t_llm.ms(), "total": t_all.ms()}

    parsed["request_id"] = rid
    return _resp(200, rid, parsed)


def _resp(code: int, rid: str, obj: dict) -> func.HttpResponse:
    resp = func.HttpResponse(
        body=json.dumps(obj, ensure_ascii=False),
        status_code=code,
        mimetype="application/json"
    )
    resp.headers["x-request-id"] = rid
    return resp
