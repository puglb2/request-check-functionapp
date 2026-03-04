# engine/checklist.py

HIPAA_CHECKLIST = [
    {"id": "REQ_NAME", "question": "Name"},
    {"id": "REQ_SSN", "question": "SS#"},
    {"id": "REQ_DOB", "question": "Date of Birth"},
    {
        "id": "REQ_SENSITIVE_PHRASE",
        "question": "Does the authorization have the phrase communicable diseases / HIV / AIDS / mental illness / chemical and/or alcohol dependency"
    },
    {"id": "REQ_LOR", "question": "Do you have a letter of representation"},
    {"id": "REQ_BILLING", "question": "Is the authorization allowing for the release and are they asking for BILLING"},
    {"id": "REQ_INFO_DESC", "question": "A description of the information to be used and disclosed (dates/part of record). Did we copy the correct information?"},
    {"id": "REQ_PROVIDER_DISCLOSER", "question": "Identification of persons/class authorized to make the use/disclosure (PHYSICIAN)"},
    {"id": "REQ_RECIPIENT", "question": "Identification of persons/class to whom disclosure is authorized (REQUESTER)"},
    {"id": "REQ_PURPOSE", "question": "Description of each purpose of use/disclosure (WHY ARE THE DOCUMENTS NEEDED)"},
    {"id": "REQ_EXPIRATION", "question": "An expiration date or event"},
    {"id": "REQ_SIGNATURE_DATE", "question": "The individual's signature and date (verified with the Medical Record)"},
    {"id": "REQ_AUTHORITY_DOC", "question": "Documentation/POA/etc showing authority to act for individual (if not patient signed)"},
    {"id": "REQ_REVOKE", "question": "Statement individual may revoke authorization in writing + right to revoke info"},
    {"id": "REQ_REDISCLOSE", "question": "Statement about potential for PHI to be redisclosed by recipient"},
]
