import os
import base64

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


def extract_text(file_input) -> str:

    endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    key = os.getenv("DOC_INTEL_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing DOC_INTEL_ENDPOINT or DOC_INTEL_KEY")

    # Handle bytes or base64
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

    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    poller = client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=file_bytes
    )

    result = poller.result()

    full_text = []

    for page in result.pages:
        if page.lines:
            for line in page.lines:
                full_text.append(line.content)

    return "\n".join(full_text)
