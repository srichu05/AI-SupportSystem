#!/usr/bin/env python3
"""
Automated Data Validation Script for CBC 2.0
Validates integrity, schema conformity, unique identifiers, syntax,
and policy status constraints for all collected datasets.
"""

import sys
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

ALLOWED_STATUSES = {
    "covered",
    "partially_covered",
    "uncovered",
    "prohibited",
    "conflict",
    "needs_human_review",
}


def validate_source_audit(errors: list) -> int:
    path = DATA_DIR / "source_audit.csv"
    if not path.exists():
        errors.append(f"Missing file: {path}")
        return 0

    expected_headers = [
        "source_id", "publisher", "url", "source_type", "intended_use",
        "retrieved_date", "retrieval_status", "license_status",
        "privacy_risk", "verification_notes"
    ]

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != expected_headers:
            errors.append(
                f"source_audit.csv header mismatch. Expected: {expected_headers}, got: {reader.fieldnames}"
            )
        rows = list(reader)

    if len(rows) < 2:
        errors.append(f"source_audit.csv has fewer than 2 rows (found {len(rows)})")

    ids = set()
    for i, r in enumerate(rows, 1):
        sid = r.get("source_id", "")
        if not sid:
            errors.append(f"source_audit.csv row {i} missing source_id")
        if sid in ids:
            errors.append(f"source_audit.csv duplicate source_id: {sid}")
        ids.add(sid)

        url = r.get("url", "")
        if not url.startswith("http"):
            errors.append(f"source_audit.csv row {i} invalid URL: {url}")

        if not r.get("retrieval_status"):
            errors.append(f"source_audit.csv row {i} missing retrieval_status")

    print(f"  [PASS] source_audit.csv validated ({len(rows)} sources)")
    return len(rows)


ALLOWED_PROVENANCE_TYPES = {"synthetic", "public_benchmark"}


def validate_policy_documents(errors: list):
    pol_dir = DATA_DIR / "policy_documents"
    raw_html_dir = pol_dir / "raw_html"

    expected_files = [
        (raw_html_dir / "zappos_shipping_and_returns.html", 5000),
        (raw_html_dir / "zappos_conditions_of_use.html", 5000),
        (raw_html_dir / "zappos_general_questions.html", 5000),
        (raw_html_dir / "zappos_customer_service_hub.html", 5000),
        (raw_html_dir / "zappos_vip_terms.html", 5000),
        (raw_html_dir / "zappos_privacy_policy.html", 5000),
        (raw_html_dir / "zappos_price_matching.html", 5000),
        (pol_dir / "zappos_shipping_and_returns.txt", 1000),
        (pol_dir / "zappos_conditions_of_use.txt", 1000),
        (pol_dir / "zappos_general_questions.txt", 1000),
        (pol_dir / "zappos_customer_service_hub.txt", 1000),
        (pol_dir / "zappos_vip_terms.txt", 1000),
        (pol_dir / "zappos_privacy_policy.txt", 1000),
        (pol_dir / "zappos_price_matching.txt", 1000),
    ]

    for p, min_size in expected_files:
        if not p.exists():
            errors.append(f"Missing policy document: {p}")
        elif p.stat().st_size < min_size:
            errors.append(f"Policy document {p.name} too small ({p.stat().st_size} bytes)")
        else:
            print(f"  [PASS] {p.name} verified ({p.stat().st_size} bytes)")

    # Verify substantive price matching policy text
    pm_path = pol_dir / "zappos_price_matching.txt"
    if pm_path.exists():
        pm_text = pm_path.read_text(encoding="utf-8")
        if "Price Guarantee" not in pm_text or "10 calendar days" not in pm_text:
            errors.append("zappos_price_matching.txt missing Price Guarantee policy text")
        if "auction" not in pm_text.lower() or "third-party" not in pm_text.lower():
            errors.append("zappos_price_matching.txt missing auction/third-party exclusion text")
        print("  [PASS] zappos_price_matching.txt substantive policy content verified")

    # Verify no duplicate button artifact in customer service hub
    csh_path = pol_dir / "zappos_customer_service_hub.txt"
    if csh_path.exists():
        csh_text = csh_path.read_text(encoding="utf-8")
        if "Sign In to Start a Return Sign In to Start a Return" in csh_text:
            errors.append("zappos_customer_service_hub.txt contains duplicated button text artifact")
        else:
            print("  [PASS] zappos_customer_service_hub.txt clean of duplicate responsive button labels")


def validate_development_complaints(errors: list) -> int:
    path = DATA_DIR / "raw" / "development_complaints.csv"
    if not path.exists():
        errors.append(f"Missing file: {path}")
        return 0

    expected_headers = [
        "case_id", "complaint_text", "issue_categories",
        "expected_status", "expected_action", "expected_escalation", "notes",
        "provenance_type"
    ]

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != expected_headers:
            errors.append(
                f"development_complaints.csv header mismatch. Expected: {expected_headers}, got: {reader.fieldnames}"
            )
        rows = list(reader)

    if len(rows) < 10:
        errors.append(f"development_complaints.csv has fewer than 10 cases (found {len(rows)})")

    case_ids = set()
    prov_counts = {"synthetic": 0, "public_benchmark": 0}
    for i, r in enumerate(rows, 1):
        cid = r.get("case_id", "")
        if not cid:
            errors.append(f"development_complaints.csv row {i} missing case_id")
        if cid in case_ids:
            errors.append(f"development_complaints.csv duplicate case_id: {cid}")
        case_ids.add(cid)

        text = r.get("complaint_text", "")
        if len(text.strip()) < 15:
            errors.append(f"development_complaints.csv {cid} complaint_text too short")

        status = r.get("expected_status", "")
        if status not in ALLOWED_STATUSES:
            errors.append(f"development_complaints.csv {cid} invalid status: {status}")

        if not r.get("expected_action"):
            errors.append(f"development_complaints.csv {cid} missing expected_action")

        prov = r.get("provenance_type", "")
        if prov not in ALLOWED_PROVENANCE_TYPES:
            errors.append(f"development_complaints.csv {cid} invalid provenance_type: '{prov}'")
        else:
            prov_counts[prov] += 1

        if cid.startswith("CMP-BITEXT-"):
            if prov != "public_benchmark":
                errors.append(f"development_complaints.csv {cid} expected provenance_type 'public_benchmark', got '{prov}'")
        elif cid.startswith("CMP-"):
            if prov != "synthetic":
                errors.append(f"development_complaints.csv {cid} expected provenance_type 'synthetic', got '{prov}'")

    print(
        f"  [PASS] development_complaints.csv validated ({len(rows)} cases, unique IDs, "
        f"provenance: {prov_counts['synthetic']} synthetic, {prov_counts['public_benchmark']} public_benchmark)"
    )
    return len(rows)


def validate_evaluation_cases(errors: list) -> int:
    path = DATA_DIR / "evaluation" / "evaluation_cases.jsonl"
    if not path.exists():
        errors.append(f"Missing file: {path}")
        return 0

    required_fields = [
        "case_id", "complaint", "expected_issues", "expected_status",
        "expected_action", "required_evidence_topics", "expected_escalation",
        "reasoning_for_label"
    ]

    records = []
    case_ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception as e:
                errors.append(f"evaluation_cases.jsonl line {line_no} invalid JSON: {e}")
                continue

            records.append(rec)
            cid = rec.get("case_id", "")
            if not cid:
                errors.append(f"evaluation_cases.jsonl line {line_no} missing case_id")
            if cid in case_ids:
                errors.append(f"evaluation_cases.jsonl duplicate case_id: {cid}")
            case_ids.add(cid)

            for rf in required_fields:
                if rf not in rec or rec[rf] is None or (isinstance(rec[rf], str) and not rec[rf].strip()):
                    errors.append(f"evaluation_cases.jsonl {cid} missing or empty field: {rf}")

            status = rec.get("expected_status", "")
            if status not in ALLOWED_STATUSES:
                errors.append(f"evaluation_cases.jsonl {cid} invalid status: {status}")

            issues = rec.get("expected_issues", [])
            if not isinstance(issues, list) or len(issues) == 0:
                errors.append(f"evaluation_cases.jsonl {cid} expected_issues must be non-empty list")

            topics = rec.get("required_evidence_topics", [])
            if not isinstance(topics, list) or len(topics) == 0:
                errors.append(f"evaluation_cases.jsonl {cid} required_evidence_topics must be non-empty list")

    if len(records) < 10:
        errors.append(f"evaluation_cases.jsonl has fewer than 10 records (found {len(records)})")

    print(f"  [PASS] evaluation_cases.jsonl validated ({len(records)} records, schema conformant)")
    return len(records)


def validate_adversarial_cases(errors: list) -> int:
    path = DATA_DIR / "evaluation" / "adversarial_cases.jsonl"
    if not path.exists():
        errors.append(f"Missing file: {path}")
        return 0

    required_fields = [
        "case_id", "adversarial_type", "complaint", "expected_status",
        "expected_safety_action", "expected_escalation", "reasoning_for_label"
    ]

    records = []
    case_ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception as e:
                errors.append(f"adversarial_cases.jsonl line {line_no} invalid JSON: {e}")
                continue

            records.append(rec)
            cid = rec.get("case_id", "")
            if not cid:
                errors.append(f"adversarial_cases.jsonl line {line_no} missing case_id")
            if cid in case_ids:
                errors.append(f"adversarial_cases.jsonl duplicate case_id: {cid}")
            case_ids.add(cid)

            for rf in required_fields:
                if rf not in rec or rec[rf] is None or (isinstance(rec[rf], str) and not rec[rf].strip()):
                    errors.append(f"adversarial_cases.jsonl {cid} missing or empty field: {rf}")

            status = rec.get("expected_status", "")
            if status not in ALLOWED_STATUSES:
                errors.append(f"adversarial_cases.jsonl {cid} invalid status: {status}")

            if rec.get("expected_escalation") is not True:
                errors.append(f"adversarial_cases.jsonl {cid} expected_escalation must be True for safety")

    if len(records) < 8:
        errors.append(f"adversarial_cases.jsonl has fewer than 8 records (found {len(records)})")

    print(f"  [PASS] adversarial_cases.jsonl validated ({len(records)} records, escalation invariant satisfied)")
    return len(records)


def main():
    print("=" * 70)
    print("CBC 2.0 — Dataset Integrity and Schema Validation")
    print("=" * 70)

    errors = []
    src_count = validate_source_audit(errors)
    validate_policy_documents(errors)
    cmp_count = validate_development_complaints(errors)
    eval_count = validate_evaluation_cases(errors)
    adv_count = validate_adversarial_cases(errors)

    print("\n" + "=" * 70)
    if errors:
        print(f"[FAIL] {len(errors)} validation error(s) detected:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("[SUCCESS] All data validation checks passed with zero errors!")
        print(f"- Registered Policy Sources: {src_count}")
        print(f"- Raw Development Complaints: {cmp_count}")
        print(f"- Labelled Evaluation Cases: {eval_count}")
        print(f"- Adversarial Safety Cases: {adv_count}")
    print("=" * 70)


if __name__ == "__main__":
    main()
