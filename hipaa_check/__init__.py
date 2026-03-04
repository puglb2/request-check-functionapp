import azure.functions as func
import json
import re

from shared.logging_utils import get_request_id
from shared.docintel import extract_text


def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)

    # -----------------------------
    # READ RAW FILE BYTES
    # -----------------------------
    file_bytes = req.get_body()

    if not file_bytes:
        return _resp(400, rid, {"error": "File required"})

    try:
        ocr_text = extract_text(file_bytes)
    except Exception as e:
        return _resp(500, rid, {
            "error": "OCR failed",
            "details": str(e)
        })

    # -----------------------------
    # CLEAN OCR TEXT
    # -----------------------------
    ocr_text = re.sub(r'\r', '', ocr_text)
    ocr_text = re.sub(r'\n+', '\n', ocr_text)
    ocr_text = re.sub(r'[ \t]+', ' ', ocr_text)

    # -----------------------------
    # RETURN PREVIEW FOR DEBUG
    # -----------------------------
    return _resp(200, rid, {
        "request_id": rid,
        "file_size": len(file_bytes),
        "ocr_length": len(ocr_text),
        "ocr_preview": ocr_text[:12000]
    })


def _resp(code: int, rid: str, obj: dict) -> func.HttpResponse:
    resp = func.HttpResponse(
        body=json.dumps(obj, ensure_ascii=False),
        status_code=code,
        mimetype="application/json"
    )
    resp.headers["x-request-id"] = rid
    return resp
