import azure.functions as func
import json
import re

from shared.logging_utils import Timer, get_request_id
from shared.docintel import extract_text
from shared.openai_client import chat_json

from engine.prompts import HIPAA_FACTS_SYSTEM
from engine.rules import run_full_hipaa_rules, score_results
from engine.signature_vision import classify_signature_from_pdf


def main(req: func.HttpRequest) -> func.HttpResponse:

    rid = get_request_id(req)
    t_all = Timer()

    if not req.files:
        return _resp(400, rid, {"error": "File required"})

    file = req.files.get("file")

    if not file:
        return _resp(400, rid, {"error": "File missing"})

    pdf_bytes = file.read()

    # -----------------------------
    # OCR
    # -----------------------------

    try:
        ocr_text = extract_text(pdf_bytes)

    except Exception as e:
        return _resp(500, rid, {"error": "OCR failed", "details": str(e)})

    ocr_text = re.sub(r'\r', '', ocr_text)
    ocr_text = re.sub(r'\n+', '\n', ocr_text)

    # -----------------------------
    # SIGNATURE VISION
    # -----------------------------

    signature = classify_signature_from_pdf(pdf_bytes)

    # -----------------------------
    # LLM EXTRACTION
    # -----------------------------

    raw = chat_json(
        HIPAA_FACTS_SYSTEM,
        f"DOCUMENT TEXT:\n{ocr_text[:16000]}",
        schema_hint={"type": "object"},
        temperature=0
    )

    content = raw["choices"][0]["message"]["content"]

    facts = json.loads(content)

    # override patient_signed if vision says not handwritten
    if signature["signature_type"] != "handwritten":
        facts["patient_signed"] = False

    # -----------------------------
    # RULE ENGINE
    # -----------------------------

    results = run_full_hipaa_rules(facts)

    percent, risk = score_results(results)

    missing = [
        r["id"] for r in results if r["status"] == "missing"
    ]

    return _resp(200, rid, {
        "request_id": rid,
        "signature": signature,
        "compliance_score": percent,
        "risk_level": risk,
        "missing_items": missing,
        "results": results,
        "facts": facts
    })


def _resp(code, rid, obj):

    resp = func.HttpResponse(
        body=json.dumps(obj),
        status_code=code,
        mimetype="application/json"
    )

    resp.headers["x-request-id"] = rid

    return resp
