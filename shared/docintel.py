import os
import base64
from pdf2image import convert_from_bytes

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


def extract_text(file_bytes) -> str:

    endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    key = os.getenv("DOC_INTEL_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing DOC_INTEL_ENDPOINT or DOC_INTEL_KEY")

    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    # Convert PDF → images
    images = convert_from_bytes(file_bytes)

    full_text = []

    for img in images:

        img_bytes = img.tobytes()

        poller = client.begin_analyze_document(
            model_id="prebuilt-read",
            body=img_bytes
        )

        result = poller.result()

        if result.content:
            full_text.append(result.content)

    return "\n".join(full_text)
