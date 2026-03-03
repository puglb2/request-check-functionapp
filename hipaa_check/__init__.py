import azure.functions as func
import json

from shared.logging_utils import Timer, get_request_id, log_json, safe_len
from shared.openai_client import chat_json, OpenAIError
#from shared.docintel import extract_text
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
    try:
        return func.HttpResponse(
            json.dumps({"step": "function started"}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"fatal_error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


def _resp(code: int, rid: str, obj: dict) -> func.HttpResponse:
    resp = func.HttpResponse(
        body=json.dumps(obj, ensure_ascii=False),
        status_code=code,
        mimetype="application/json"
    )
    resp.headers["x-request-id"] = rid
    return resp
