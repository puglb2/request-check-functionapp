import azure.functions as func
import os
import datetime
from shared.logging_utils import get_request_id

def main(req: func.HttpRequest) -> func.HttpResponse:
    rid = get_request_id(req)
    body = {
        "ok": True,
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "version": os.getenv("APP_VERSION", "0.0.0"),
    }
    resp = func.HttpResponse(
        body=str(body).replace("'", '"'),
        status_code=200,
        mimetype="application/json"
    )
    resp.headers["x-request-id"] = rid
    return resp
