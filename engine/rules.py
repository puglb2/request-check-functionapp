# engine/rules.py

def _result(item_id: str, status: str, evidence: str):
    return {"id": item_id, "status": status, "evidence": evidence or ""}


def run_doc_kind_rules(facts: dict):
    """
    Independent of order_type:
    - subpoena -> satisfactory assurance
    - workers_comp -> wording indicates workers comp
    - disability -> 1699 form
    """

    results = []

    doc_kind = facts.get("doc_kind", "unknown")
    ev = (facts.get("evidence") or {})

    if doc_kind == "subpoena":
        v = facts.get("has_satisfactory_assurance")
        if v is True:
            results.append(_result("SUBPOENA_SATISFACTORY_ASSURANCE", "present", ev.get("has_satisfactory_assurance", "")))
        elif v is False:
            results.append(_result("SUBPOENA_SATISFACTORY_ASSURANCE", "missing", ev.get("has_satisfactory_assurance", "")))
        else:
            results.append(_result("SUBPOENA_SATISFACTORY_ASSURANCE", "unclear", ev.get("has_satisfactory_assurance", "")))

    if doc_kind == "workers_comp":
        v = facts.get("has_workers_comp_wording")
        if v is True:
            results.append(_result("WORKERS_COMP_WORDING", "present", ev.get("has_workers_comp_wording", "")))
        elif v is False:
            results.append(_result("WORKERS_COMP_WORDING", "missing", ev.get("has_workers_comp_wording", "")))
        else:
            results.append(_result("WORKERS_COMP_WORDING", "unclear", ev.get("has_workers_comp_wording", "")))

    if doc_kind == "disability":
        v = facts.get("has_1699_form")
        if v is True:
            results.append(_result("DISABILITY_1699_FORM", "present", ev.get("has_1699_form", "")))
        elif v is False:
            results.append(_result("DISABILITY_1699_FORM", "missing", ev.get("has_1699_form", "")))
        else:
            results.append(_result("DISABILITY_1699_FORM", "unclear", ev.get("has_1699_form", "")))

    return results


def run_signature_delegation_rules(facts: dict):
    """
    - If patient did NOT sign, must have authority-to-sign documentation.
    - If requestor isn't the entity needing records, require letter of rep.
      Exception: if on behalf of patient AND patient signed -> LoR not required.
    """
    results = []
    ev = (facts.get("evidence") or {})

    patient_signed = facts.get("patient_signed")
    has_authority = facts.get("has_authority_to_sign_doc")

    if patient_signed is False:
        if has_authority is True:
            results.append(_result("AUTHORITY_TO_SIGN", "present", ev.get("has_authority_to_sign_doc", "")))
        elif has_authority is False:
            results.append(_result("AUTHORITY_TO_SIGN", "missing", ev.get("has_authority_to_sign_doc", "")))
        else:
            results.append(_result("AUTHORITY_TO_SIGN", "unclear", ev.get("has_authority_to_sign_doc", "")))

    on_behalf = facts.get("request_on_behalf_of_patient")
    has_lor = facts.get("has_letter_of_rep")

    # If we know it is on behalf of patient AND patient signed -> LoR not required
    if on_behalf is True and patient_signed is True:
        results.append(_result("LETTER_OF_REP", "present", "Not required (patient signed and request is on behalf of patient)."))
        return results

    # Otherwise, if unclear, treat as standard LoR expectation
    if has_lor is True:
        results.append(_result("LETTER_OF_REP", "present", ev.get("has_letter_of_rep", "")))
    elif has_lor is False:
        results.append(_result("LETTER_OF_REP", "missing", ev.get("has_letter_of_rep", "")))
    else:
        results.append(_result("LETTER_OF_REP", "unclear", ev.get("has_letter_of_rep", "")))

    return results


def score_results(results):
    score = 0.0
    total = len(results)

    for r in results:
        if r.get("status") == "present":
            score += 1.0
        elif r.get("status") == "unclear":
            score += 0.5

    pct = round((score / total) * 100, 2) if total else 0.0

    if pct >= 90:
        risk = "low"
    elif pct >= 70:
        risk = "moderate"
    else:
        risk = "high"

    return pct, risk
