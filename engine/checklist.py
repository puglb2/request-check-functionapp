HIPAA_CHECKLIST = [
    # BASIC CONTEXT FLAGS
    {"id": "is_subpoena", "question": "Authorization present if not court order"},
    {"id": "is_workers_comp", "question": "File number or authorization present"},
    {"id": "is_disability", "question": "Disability request present"},

    # CORE HIPAA REQUIREMENTS
    {"id": "name", "question": "Patient name present"},
    {"id": "ssn", "question": "SSN present"},
    {"id": "dob", "question": "Date of birth present"},

    {"id": "sensitive_clause", "question": "Authorization includes HIV/AIDS, mental illness, substance abuse clause"},
    {"id": "letter_of_rep", "question": "Letter of representation present"},
    {"id": "billing_request", "question": "Authorization allows release and billing request present"},

    {"id": "info_description", "question": "Specific description of info to be disclosed"},
    {"id": "authorized_discloser", "question": "Who can disclose PHI identified"},
    {"id": "authorized_receiver", "question": "Who receives PHI identified"},

    {"id": "purpose", "question": "Purpose of disclosure stated"},
    {"id": "expiration", "question": "Expiration date or event present"},

    {"id": "signature", "question": "Signature and date present"},
    {"id": "authority_docs", "question": "Authority documentation present (POA, etc.)"},

    {"id": "revocation", "question": "Right to revoke stated"},
    {"id": "redisclosure", "question": "Redisclosure risk stated"}
]
