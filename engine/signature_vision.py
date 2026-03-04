# engine/signature_vision.py

import io

import fitz  # PyMuPDF
import numpy as np
from PIL import Image


def classify_signature_from_pdf(pdf_bytes: bytes) -> dict:
    """
    Heuristic pixel-based signature classification:
    - Renders pages to images
    - Looks for "ink-like" dense dark strokes (handwritten-ish)
    - This is NOT identity matching; it's typed-vs-handwritten screening.
    """

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    best = {
        "signature_type": "unknown",  # handwritten|typed|unknown
        "confidence": "low",
        "notes": ""
    }

    # Render at a decent DPI for stroke visibility
    zoom = 2.0
    mat = fitz.Matrix(zoom, zoom)

    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        arr = np.array(img)

        # Convert to grayscale quickly
        gray = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.uint8)

        # "Ink" heuristic: count very dark pixels
        dark = np.sum(gray < 60)

        # If there’s substantial ink-like content, flag handwritten-ish
        if dark > 25000:
            best = {
                "signature_type": "handwritten",
                "confidence": "med",
                "notes": f"Page {i+1} has high dark-pixel density consistent with pen strokes."
            }
            break

    return best
