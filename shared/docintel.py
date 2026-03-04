import os
import base64

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


def extract_text(file_input) -> str:

    endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    key = os.getenv("DOC_INTEL_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing DOC_INTEL_ENDPOINT or DOC_INTEL_KEY")

    # -----------------------------
    # HANDLE INPUT TYPES
    # -----------------------------
    if isinstance(file_input, bytes):

        try:
            decoded = base64.b64decode(file_input, validate=True)

            if decoded.startswith(b"%PDF"):
                file_bytes = decoded
            else:
                file_bytes = file_input

        except Exception:
            file_bytes = file_input

    elif isinstance(file_input, str):
        file_bytes = base64.b64decode(file_input)

    else:
        raise RuntimeError("Unsupported document input type")

    # -----------------------------
    # CREATE CLIENT
    # -----------------------------
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    # -----------------------------
    # RUN OCR
    # -----------------------------
    poller = client.begin_analyze_document(
        "prebuilt-read",
        analyze_request=file_bytes,
        content_type="application/pdf"
    )

    result = poller.result()

    # -----------------------------
    # RETURN FULL TEXT
    # -----------------------------
    text_output = result.content or ""

    return text_output
