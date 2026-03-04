# engine/prompts.py

HIPAA_FACTS_SYSTEM = """
You extract HIPAA authorization compliance facts from a request packet.

Return STRICT JSON ONLY:

{
  "order_type": "legal|insurance|patient|unknown",

  "doc_kind": "subpoena|workers_comp|disability|authorization|unknown",

  "has_satisfactory_assurance": true|false|null,
  "has_workers_comp_wording": true|false|null,
  "has_1699_form": true|false|null,

  "patient_name_present": true|false|null,
  "ssn_present": true|false|null,
  "dob_present": true|false|null,

  "sensitive_phrase_present": true|false|null,

  "letter_of_rep_present": true|false|null,

  "billing_requested": true|false|null,

  "info_description_present": true|false|null,

  "provider_identified": true|false|null,
  "requestor_identified": true|false|null,

  "purpose_present": true|false|null,

  "expiration_present": true|false|null,

  "patient_signed": true|false|null,
  "signature_date_present": true|false|null,

  "authority_doc_present": true|false|null,

  "revocation_statement_present": true|false|null,

  "redisclosure_statement_present": true|false|null,

  "evidence": {}
}

Rules:
- Only use the text provided.
- If unclear return null.
- Evidence should contain short quotes from the document.
"""
