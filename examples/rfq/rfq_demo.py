#!/usr/bin/env python3
"""RFQ line-item extraction demo — proof-of-approach for the n8n Community RFQ thread.

Reads a text-based RFQ file, extracts line items (code, description, qty, unit),
and prints them as CSV-ready rows. Pure stdlib. Deterministic parser first;
lines that fail the pattern are flagged NEEDS_REVIEW (LLM pass would go there).

Usage: python3 rfq_demo.py sample_rfq.txt
"""
import re
import sys

# Typical RFQ line patterns seen in electrical parts distributor quotes
LINE_PATTERNS = [
    # "1. ABB SACE S3N 250A circuit breaker, qty 4" (no unit given)
    re.compile(
        r"^(?P<idx>\d+)[.)]\s+(?P<desc>.+?),\s*(?:qty|quantity)\s*(?P<qty>\d+)\s*$",
        re.I,
    ),
    # "1. ABB SACE S3N 250A circuit breaker, qty 4 pcs"
    re.compile(
        r"^(?P<idx>\d+)[.)]\s+(?P<desc>.+?),\s*(?:qty|quantity)\s*(?P<qty>\d+)\s*(?P<unit>[a-zA-Z]+)\s*$",
        re.I,
    ),
    # "4 x ABB SACE S3N 250A — circuit breaker"
    re.compile(
        r"^(?P<qty>\d+)\s*[x×]\s*(?P<desc>.+?)(?:\s*[—–-]\s*(?P<note>.*))?$",
        re.I,
    ),
    # "A9F74410 2 EA Circuit breaker iC60N 4P 40A"
    re.compile(
        r"^(?P<code>[A-Z0-9][A-Z0-9\-/]{3,})\s+(?P<qty>\d+)\s+(?P<unit>EA|PCS|PC|SET|BOX|M|KG)\s+(?P<desc>.+)$",
        re.I,
    ),
    # "Hager MB112N 10 PCS Distribution board" (brand + code + qty + unit + desc)
    re.compile(
        r"^(?P<brand>[A-Z][A-Za-z]+)\s+(?P<code>[A-Z0-9][A-Z0-9\-/]{3,})\s+(?P<qty>\d+)\s+(?P<unit>EA|PCS|PC|SET|BOX|M|KG)\s+(?P<desc>.+)$",
    ),
    # "Siemens 3RV2011-1CA10 motor starter, qty 6" (brand + code + desc, qty at end)
    re.compile(
        r"^(?P<brand>[A-Z][A-Za-z]+)\s+(?P<code>[A-Z0-9][A-Z0-9\-/]{3,})\s+(?P<desc>.+?),\s*(?:qty|quantity)\s*(?P<qty>\d+)\s*$",
        re.I,
    ),
    # "Phoenix Contact UT 2,5 terminal blocks, qty 200" (brand 2 words + code + desc, qty at end)
    re.compile(
        r"^(?P<brand>[A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+)\s+(?P<code>[A-Z0-9][A-Z0-9\-/.,]{2,})\s+(?P<desc>.+?),\s*(?:qty|quantity)\s*(?P<qty>\d+)\s*$",
        re.I,
    ),
]

UNIT_ALIASES = {"pcs": "EA", "pc": "EA", "pieces": "EA", "set": "SET", "box": "BOX"}


def normalize_unit(u: str) -> str:
    u = u.strip().upper()
    return UNIT_ALIASES.get(u.lower(), u)


def normalize_code(code: str) -> str:
    return re.sub(r"[\s\-_/]", "", code).upper()


def parse_line(line: str):
    line = line.strip()
    if not line:
        return None
    # skip greeting/signature lines entirely (not line items)
    if re.match(r"^(dear|hello|please find|regards|best|purchasing|sincerely|thank)", line, re.I) or line.endswith(":"):
        return None
    for pat in LINE_PATTERNS:
        m = pat.match(line)
        if m:
            d = m.groupdict()
            brand = d.get("brand")
            desc = (d.get("desc") or d.get("note") or "").strip()
            if brand:
                desc = f"{brand} {desc}".strip()
            return {
                "code": normalize_code(d.get("code", "")) or None,
                "description": desc,
                "qty": int(d.get("qty", 0)),
                "unit": normalize_unit(d.get("unit") or "EA"),
                "confidence": "HIGH",
            }
    return {
        "code": None,
        "description": line,
        "qty": None,
        "unit": None,
        "confidence": "NEEDS_REVIEW",
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    rows = []
    with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
        for raw in f:
            item = parse_line(raw)
            if item:
                rows.append(item)
    w = (len(r["description"]) for r in rows)
    print("code,description,qty,unit,confidence")
    for r in rows:
        print(f"{r['code'] or ''},{r['description']},{r['qty'] or ''},{r['unit'] or ''},{r['confidence']}")
    review = sum(1 for r in rows if r["confidence"] == "NEEDS_REVIEW")
    print(f"\n{len(rows)} line items parsed; {review} flagged NEEDS_REVIEW", file=sys.stderr)


if __name__ == "__main__":
    main()