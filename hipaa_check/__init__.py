import azure.functions as func
import json
import re

from shared.logging_utils import Timer, get_request_id, log_json, safe_len
from shared.openai_client import chat_json, OpenAIError
from shared.docintel import extract_text
from engine.checklist import HIPAA_CHECKLIST


SYSTEM_PROMPT = """
You are a HIPAA compliance evaluation engine.

For each checklist item:
- Determine if it is PRESENT, MISSING, or UNCLEAR
- Base ONLY on the provided text
- Do NOT guess.

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

    checklist_text = "\n".join([
        f"- {item['id']}: {item['question']}"
        for item in HIPAA_CHECKLIST
    ])

    return f"""
CHECKLIST:
{checklist_text}

DOCUMENT TEXT:
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

    # -----------------------------
    # GET FILE BYTES
    # -----------------------------

    file_bytes = None

    try:
        if req.files:
            file = req.files.get("file")
            if file:
                file_bytes = file.read()
    except Exception:
        pass

    if not file_bytes:
        file_bytes = req.get_body()

    if not file_bytes:
        return _resp(400, rid, {"error": "File required"})

    # -----------------------------
    # OCR
    # -----------------------------

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

    log_json("hipaa_check.request", {
        "request_id": rid,
        "ocr_chars": safe_len(ocr_text)
    })

    # -----------------------------
    # BUILD PROMPT
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

        log_json("hipaa_check.openai_error", {
            "request_id": rid,
            "error": str(e)
        })

        return _resp(502, rid, {
            "error": "Model call failed",
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

    if req.params.get("debug") == "1":
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
