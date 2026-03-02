import azure.functions as func
import json
from shared.logging_utils import get_request_id
from engine.checklist import HIPAA_CHECKLIST

def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)
    resp = func.HttpResponse(
        json.dumps({"ok": True, "step": "B", "checklist_len": len(HIPAA_CHECKLIST)}),
        mimetype="application/json",
        status_code=200
    )
    resp.headers["x-request-id"] = rid
    return resp
