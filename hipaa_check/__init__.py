import azure.functions as func
import json
import re

from shared.logging_utils import get_request_id
from shared.docintel import extract_text


def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)

    # -----------------------------
    # FILE UPLOAD
    # -----------------------------
    if not req.files:
        return _resp(400, rid, {"error": "File required"})

    file = req.files.get("file")

    if not file:
        return _resp(400, rid, {"error": "File missing"})

    try:
        ocr_text = extract_text(file.read())
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
        "ocr_length": len(ocr_text),
        "ocr_preview": ocr_text[-2000:]
    })


def _resp(code: int, rid: str, obj: dict) -> func.HttpResponse:
    resp = func.HttpResponse(
        body=json.dumps(obj, ensure_ascii=False),
        status_code=code,
        mimetype="application/json"
    )
    resp.headers["x-request-id"] = rid
    return resp
