import azure.functions as func
import json

from shared.logging_utils import Timer, get_request_id, log_json, safe_len
from shared.openai_client import chat_json, OpenAIError
from shared.docintel import extract_text
from engine.checklist import HIPAA_CHECKLIST


SYSTEM_PROMPT = """
You are a HIPAA compliance evaluation engine.

For each checklist item:
- Determine if it is PRESENT, MISSING, or UNCLEAR
- Base ONLY on the provided text
- Do NOT guess

Return STRICT JSON:
{
  "results": [
    {
      "id": "...",
      "status": "present | missing | unclear",
      "evidence": "short quote or reason"
    }
  ]
}
"""


def build_user_prompt(ocr_text: str) -> str:
    checklist_text = "\n".join(
        [f"- {item['id']}: {item['question']}" for item in HIPAA_CHECKLIST]
    )

    return f"""
CHECKLIST:
{checklist_text}

OCR TEXT:
{ocr_text[:12000]}
"""


def score_results(results):
    score = 0
    total = len(results)

    for r in results:
        status = r.get("status")
        if status == "present":
            score += 1
        elif status == "unclear":
            score += 0.5

    percent = round((score / total) * 100, 2) if total else 0

    if percent >= 90:
        risk = "low"
    elif percent >= 70:
        risk = "moderate"
    else:
        risk = "high"

    return percent, risk


def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)
    t_all = Timer()
    debug = req.params.get("debug") == "1"

    ocr_text = None

    # -----------------------------
    # FILE UPLOAD (OCR)
    # -----------------------------
    if req.files:
        file = req.files.get("file")

        if not file:
            return _resp(400, rid, {
                "error": "File missing",
                "request_id": rid
            })

        file_bytes = file.read()

        try:
            ocr_text = extract_text(file_bytes)
        except Exception as e:
            return _resp(500, rid, {
                "error": "OCR failed",
                "details": str(e),
                "request_id": rid
            })

    # -----------------------------
    # JSON TEXT INPUT
    # -----------------------------
    else:
        try:
            payload = req.get_json()
            ocr_text = payload.get("ocr_text")
        except Exception:
            return _resp(400, rid, {
                "error": "Invalid input",
                "request_id": rid
            })

    if not ocr_text:
        return _resp(400, rid, {
            "error": "No text provided",
            "request_id": rid
        })

    log_json("hipaa_check.request", {
        "request_id": rid,
        "ocr_chars": safe_len(ocr_text)
    })

    # -----------------------------
    # LLM CALL
    # -----------------------------
    user_prompt = build_user_prompt(ocr_text)
    t_llm = Timer()

    try:
        raw = chat_json(
            SYSTEM_PROMPT,
            user_prompt,
            schema_hint={"type": "object"},
            temperature=0.1
        )
    except OpenAIError as e:
        return _resp(502, rid, {
            "error": "Model call failed",
            "details": str(e),
            "request_id": rid
        })

    # -----------------------------
    # PARSE MODEL OUTPUT
    # -----------------------------
    try:
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except Exception:
        return _resp(500, rid, {
            "error": "Failed to parse model output",
            "raw_response": raw,
            "request_id": rid
        })

    results_list = parsed.get("results", [])

    percent, risk = score_results(results_list)

    missing_items = [
        r["id"] for r in results_list
        if r.get("status") == "missing"
    ]

    output = {
        "request_id": rid,
        "compliance_score": percent,
        "risk_level": risk,
        "missing_items": missing_items,
        "results": results_list
    }

    if debug:
        output["timing_ms"] = {
            "llm": t_llm.ms(),
            "total": t_all.ms()
        }

    return _resp(200, rid, output)


def _resp(code: int, rid: str, obj: dict) -> func.HttpResponse:
    resp = func.HttpResponse(
        body=json.dumps(obj, ensure_ascii=False),
        status_code=code,
        mimetype="application/json"
    )
    resp.headers["x-request-id"] = rid
    return resp
