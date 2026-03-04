# engine/prompts.py

ORDER_EXTRACT_SYSTEM = """
You extract order intake fields from a medical record request packet.

Return STRICT JSON only:
{
  "external_id": string|null,
  "order_type": "legal"|"insurance"|"patient"|"unknown",
  "dos": string|null,
  "patient_name": string|null,
  "dob": string|null,
  "pickup_provider": string|null,
  "evidence": {
    "external_id": string,
    "order_type": string,
    "dos": string,
    "patient_name": string,
    "dob": string,
    "pickup_provider": string
  }
}

Rules:
- Use only what is present in text.
- If unclear, return null/unknown.
- Evidence should be a short quote or pointer (no guessing).
"""

HIPAA_FACTS_SYSTEM = """
You extract HIPAA-compliance-relevant facts from a request packet.

Return STRICT JSON only:
{
  "order_type": "legal"|"insurance"|"patient"|"unknown",

  "doc_kind": "subpoena"|"workers_comp"|"disability"|"authorization"|"unknown",

  "has_satisfactory_assurance": true|false|null,
  "has_workers_comp_wording": true|false|null,
  "has_1699_form": true|false|null,

  "patient_signed": true|false|null,
  "request_on_behalf_of_patient": true|false|null,

  "has_letter_of_rep": true|false|null,
  "has_authority_to_sign_doc": true|false|null,

  "evidence": {
    "doc_kind": string,
    "has_satisfactory_assurance": string,
    "has_workers_comp_wording": string,
    "has_1699_form": string,
    "patient_signed": string,
    "has_letter_of_rep": string,
    "has_authority_to_sign_doc": string
  }
}

Rules:
- doc_kind is what drives the required documentation checks.
- Do not guess. Use null when unclear.
- Evidence must be short and from the text.
"""
