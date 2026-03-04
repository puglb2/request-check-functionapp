import os
import base64

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


def extract_text(file_input) -> str:
    """
    Extract OCR text from a PDF or image using Azure Document Intelligence (prebuilt-read).
    Accepts raw bytes or base64 string.
    """

    endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    key = os.getenv("DOC_INTEL_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing DOC_INTEL_ENDPOINT or DOC_INTEL_KEY")

    # -----------------------------
    # Normalize input → bytes
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
    # Create client
    # -----------------------------
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    # -----------------------------
    # Run OCR
    # -----------------------------
    poller = client.begin_analyze_document(
        model_id="prebuilt-read",
        body=file_bytes
    )

    result = poller.result()

    # -----------------------------
    # Extract full document text
    # -----------------------------
    if getattr(result, "content", None):
        return result.content

    # Fallback if content is empty
    full_text = []
    if getattr(result, "pages", None):
        for page in result.pages:
            if getattr(page, "lines", None):
                for line in page.lines:
                    full_text.append(line.content)

    return "\n".join(full_text)
