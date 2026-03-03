import azure.functions as func
import json

from shared.logging_utils import Timer, get_request_id, log_json, safe_len
from shared.openai_client import chat_json, OpenAIError
from shared.docintel import extract_text
from engine.checklist import HIPAA_CHECKLIST


SYSTEM_PROMPT_EXTRACT = """
You are extracting structured fields from medical authorization documents.

Search the ENTIRE text carefully.

Fields to extract:

1. patient_name
   - May appear after labels like:
     "Patient Name"
     "Print Name"
     "Name"
   - May appear on the next line.
   - If a full human name appears anywhere, extract it.

2. dob
   - May appear as:
     "DOB"
     "Date of Birth"
   - Extract full date if found.

3. signature_present
   - True if document appears signed.
   - If the word "signature" appears AND a handwritten or signed indication exists, return true.

4. date_signed
   - May appear as:
     "Date"
     "Date Signed"
     Near signature lines.

Important:
- Search entire document.
- Do not require strict formatting.
- If uncertain, return null.
- Do NOT hallucinate.

Return STRICT JSON only.
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


from engine.extract_fields import extract_structured_fields

def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)
    debug = req.params.get("debug") == "1"

    ocr_text = None

    # FILE UPLOAD
    if req.files:
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

    # JSON INPUT
    else:
        try:
            payload = req.get_json()
            ocr_text = payload.get("ocr_text")
        except Exception:
            return _resp(400, rid, {"error": "Invalid input"})

    if not ocr_text:
        return _resp(400, rid, {"error": "No text provided"})

    # ------------------------
    # LLM STRUCTURED EXTRACTION
    # ------------------------

    try:
        fields = extract_structured_fields(ocr_text)
    except Exception as e:
        return _resp(500, rid, {
            "error": "Field extraction failed",
            "details": str(e)
        })

    # ------------------------
    # DETERMINISTIC RULE ENGINE
    # ------------------------

    results = []

    def mark(id, present, evidence):
        results.append({
            "id": id,
            "status": "present" if present else "missing",
            "evidence": evidence
        })

    mark("PATIENT_NAME",
         bool(fields.get("patient_name")),
         fields.get("patient_name"))

    mark("DOB",
         bool(fields.get("dob")),
         fields.get("dob"))

    mark("SIGNATURE",
         fields.get("signature_present") is True,
         "Signature detected" if fields.get("signature_present") else "No signature found")

    mark("DATE_SIGNED",
         bool(fields.get("date_signed")),
         fields.get("date_signed"))

    total = len(results)
    present = sum(1 for r in results if r["status"] == "present")

    score = round((present / total) * 100, 2) if total else 0

    risk = "low" if score >= 90 else "moderate" if score >= 70 else "high"

    return _resp(200, rid, {
        "request_id": rid,
        "compliance_score": score,
        "risk_level": risk,
        "extracted_fields": fields,
        "results": results
    })


def _resp(code: int, rid: str, obj: dict) -> func.HttpResponse:
    resp = func.HttpResponse(
        body=json.dumps(obj, ensure_ascii=False),
        status_code=code,
        mimetype="application/json"
    )
    resp.headers["x-request-id"] = rid
    return resp
