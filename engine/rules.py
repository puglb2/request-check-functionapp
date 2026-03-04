# engine/rules.py


def result(id, status, evidence=""):
    return {
        "id": id,
        "status": status,
        "evidence": evidence
    }


def evaluate_bool(id, value, evidence=""):

    if value is True:
        return result(id, "present", evidence)

    if value is False:
        return result(id, "missing", evidence)

    return result(id, "unclear", evidence)


def run_full_hipaa_rules(facts):

    results = []

    ev = facts.get("evidence", {})

    # -------------------------
    # HIPAA AUTHORIZATION ITEMS
    # -------------------------

    results.append(evaluate_bool("NAME", facts.get("patient_name_present"), ev.get("patient_name_present")))
    results.append(evaluate_bool("SSN", facts.get("ssn_present"), ev.get("ssn_present")))
    results.append(evaluate_bool("DOB", facts.get("dob_present"), ev.get("dob_present")))

    results.append(evaluate_bool("SENSITIVE_PHRASE", facts.get("sensitive_phrase_present"), ev.get("sensitive_phrase_present")))

    results.append(evaluate_bool("LETTER_OF_REP", facts.get("letter_of_rep_present"), ev.get("letter_of_rep_present")))

    results.append(evaluate_bool("BILLING_REQUESTED", facts.get("billing_requested"), ev.get("billing_requested")))

    results.append(evaluate_bool("INFO_DESCRIPTION", facts.get("info_description_present"), ev.get("info_description_present")))

    results.append(evaluate_bool("PROVIDER_IDENTIFIED", facts.get("provider_identified"), ev.get("provider_identified")))

    results.append(evaluate_bool("REQUESTOR_IDENTIFIED", facts.get("requestor_identified"), ev.get("requestor_identified")))

    results.append(evaluate_bool("PURPOSE", facts.get("purpose_present"), ev.get("purpose_present")))

    results.append(evaluate_bool("EXPIRATION", facts.get("expiration_present"), ev.get("expiration_present")))

    results.append(evaluate_bool("SIGNATURE_DATE", facts.get("signature_date_present"), ev.get("signature_date_present")))

    results.append(evaluate_bool("AUTHORITY_DOC", facts.get("authority_doc_present"), ev.get("authority_doc_present")))

    results.append(evaluate_bool("REVOCATION_STATEMENT", facts.get("revocation_statement_present"), ev.get("revocation_statement_present")))

    results.append(evaluate_bool("REDISCLOSURE_STATEMENT", facts.get("redisclosure_statement_present"), ev.get("redisclosure_statement_present")))

    # -------------------------
    # DOCUMENT TYPE RULES
    # -------------------------

    doc_kind = facts.get("doc_kind")

    if doc_kind == "subpoena":

        results.append(
            evaluate_bool(
                "SUBPOENA_SATISFACTORY_ASSURANCE",
                facts.get("has_satisfactory_assurance"),
                ev.get("has_satisfactory_assurance")
            )
        )

    if doc_kind == "workers_comp":

        results.append(
            evaluate_bool(
                "WORKERS_COMP_WORDING",
                facts.get("has_workers_comp_wording"),
                ev.get("has_workers_comp_wording")
            )
        )

    if doc_kind == "disability":

        results.append(
            evaluate_bool(
                "DISABILITY_1699_FORM",
                facts.get("has_1699_form"),
                ev.get("has_1699_form")
            )
        )

    # -------------------------
    # SIGNATURE AUTHORITY
    # -------------------------

    if facts.get("patient_signed") is False:

        results.append(
            evaluate_bool(
                "AUTHORITY_TO_SIGN",
                facts.get("authority_doc_present"),
                ev.get("authority_doc_present")
            )
        )

    return results


def score_results(results):

    score = 0
    total = len(results)

    for r in results:

        if r["status"] == "present":
            score += 1

        elif r["status"] == "unclear":
            score += 0.5

    percent = round((score / total) * 100, 2) if total else 0

    if percent >= 90:
        risk = "low"

    elif percent >= 70:
        risk = "moderate"

    else:
        risk = "high"

    return percent, risk
