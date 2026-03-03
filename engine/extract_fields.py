# engine/extract_fields.py

from shared.openai_client import chat_json

SYSTEM_PROMPT_EXTRACT = """
Extract structured fields from the document text.

Return STRICT JSON:

{
  "patient_name": string | null,
  "dob": string | null,
  "signature_present": true | false,
  "date_signed": string | null
}

Rules:
- Search entire document.
- If a label like "Print Name" appears with a value nearby, treat it as the name.
- If no value found, return null.
- signature_present = true if a signature or signed line appears.
"""


def extract_structured_fields(ocr_text: str):

    raw = chat_json(
        SYSTEM_PROMPT_EXTRACT,
        ocr_text[:12000],
        schema_hint={"type": "object"},
        temperature=0
    )

    content = raw["choices"][0]["message"]["content"]

    import json
    return json.loads(content)
