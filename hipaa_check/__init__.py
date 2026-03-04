import azure.functions as func
import json
import re

from shared.logging_utils import Timer, get_request_id, log_json, safe_len
from shared.openai_client import chat_json, OpenAIError
from shared.docintel import extract_text

from engine.prompts import HIPAA_FACTS_SYSTEM
from engine.rules import run_doc_kind_rules, run_signature_delegation_rules, score_results
from engine.signature_vision import classify_signature_from_pdf


def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)
    t_all = Timer()
    debug = req.params.get("debug") == "1"
    reviewer = req.params.get("reviewer")  # "1" or "2" optional

    if not req.files:
        return _resp(400, rid, {"error": "File required", "request_id": rid})

    f = req.files.get("file")
    if not f:
        return _resp(400, rid, {"error": "File missing", "request_id": rid})

    pdf_bytes = f.read()

    # OCR
    try:
        ocr_text = extract_text(pdf_bytes)
    except Exception as e:
        return _resp(500, rid, {"error": "OCR failed", "details": str(e), "request_id": rid})

    # Clean
    ocr_text = re.sub(r"\r", "", ocr_text)
    ocr_text = re.sub(r"\n+", "\n", ocr_text)
    ocr_text = re.sub(r"[ \t]+", " ", ocr_text)

    log_json("hipaa_check.request", {
        "request_id": rid,
        "ocr_chars": safe_len(ocr_text),
        "reviewer": reviewer
    })

    # Vision signature screening (handwritten vs typed/unknown)
    sig = classify_signature_from_pdf(pdf_bytes)

    # LLM facts extraction (no guessing)
    t_llm = Timer()
    try:
        raw = chat_json(
            HIPAA_FACTS_SYSTEM,
            f"DOCUMENT TEXT:\n{ocr_text[:16000]}",
            schema_hint={"type": "object"},
            temperature=0.0
        )
    except OpenAIError as e:
        return _resp(502, rid, {"error": "Model call failed", "details": str(e), "request_id": rid})

    try:
        content = raw["choices"][0]["message"]["content"]
        facts = json.loads(content)
    except Exception:
        return _resp(500, rid, {"error": "Failed to parse model output", "request_id": rid})

    # Override patient_signed if signature is clearly not handwritten
    # (you said typed/e-sig not acceptable)
    if sig.get("signature_type") != "handwritten":
        # If LLM said signed but vision says not handwritten, mark as false
        facts["patient_signed"] = False

    # Rules
    results = []
    results.extend(run_doc_kind_rules(facts))
    results.extend(run_signature_delegation_rules(facts))

    score, risk = score_results(results)
    missing = [r["id"] for r in results if r["status"] == "missing"]

    out = {
        "request_id": rid,
        "reviewer": reviewer,
        "order_type": facts.get("order_type"),
        "doc_kind": facts.get("doc_kind"),
        "signature": sig,
        "compliance_score": score,
        "risk_level": risk,
        "missing_items": missing,
        "results": results,
        "facts": facts
    }

    if debug:
        out["timing_ms"] = {"llm": t_llm.ms(), "total": t_all.ms()}

    return _resp(200, rid, out)


def _resp(code: int, rid: str, obj: dict) -> func.HttpResponse:
    resp = func.HttpResponse(
        body=json.dumps(obj, ensure_ascii=False),
        status_code=code,
        mimetype="application/json"
    )
    resp.headers["x-request-id"] = rid
    return resp
