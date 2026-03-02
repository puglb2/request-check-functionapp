import json
import logging
import os
import time
import uuid
from typing import Any, Dict, Optional, Tuple

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.getLogger().setLevel(LOG_LEVEL)

def get_request_id(req) -> str:
    rid = req.headers.get("x-request-id")
    return rid if rid else str(uuid.uuid4())

class Timer:
    def __init__(self):
        self._t0 = time.perf_counter()
    def ms(self) -> int:
        return int((time.perf_counter() - self._t0) * 1000)

def log_json(message: str, data: Dict[str, Any]) -> None:
    logging.info("%s %s", message, json.dumps(data, ensure_ascii=False))

def safe_len(s: Optional[str]) -> int:
    return len(s) if s else 0
