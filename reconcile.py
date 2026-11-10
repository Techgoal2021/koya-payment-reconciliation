"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path


def parse_amount(raw_amount) -> Decimal:
    if isinstance(raw_amount, str):
        cleaned = raw_amount.replace(",", "").strip()
        return Decimal(cleaned)
    return Decimal(str(raw_amount))


def parse_ts(raw_ts: str) -> datetime:
    if raw_ts.endswith("Z"):
        raw_ts = raw_ts[:-1] + "+00:00"
    return datetime.fromisoformat(raw_ts)


base_dir = Path(__file__).resolve().parent
latest_by_txn = {}

with open(base_dir / "payments.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        if not txn_id:
            continue

        try:
            ts = parse_ts(event["ts"])
            amount = parse_amount(event["amount"])
        except (KeyError, TypeError, ValueError, InvalidOperation, AttributeError):
            continue

        existing = latest_by_txn.get(txn_id)
        if existing is None or ts > existing[0]:
            latest_by_txn[txn_id] = (ts, event.get("status"), amount)

total = Decimal("0")
count = 0
for _, status, amount in latest_by_txn.values():
    if status == "success":
        total += amount
        count += 1

with open(base_dir / "expected.txt", encoding="utf-8") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
