"""Small JSONL incident register for the network troubleshooting runbooks."""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCENARIOS = Path(__file__).resolve().parents[2] / "scenarios.json"
STATUSES = ("open", "investigating", "mitigated", "resolved", "closed")


def now():
    return datetime.now(timezone.utc).isoformat()


def db_path():
    return Path(os.environ.get("INCIDENTDESK_FILE", "incidents.jsonl"))


def load_scenarios():
    return json.loads(SCENARIOS.read_text(encoding="utf-8"))


def load_records(path):
    if not path.exists():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError("invalid incident register line {}: {}".format(number, exc))
    return records


def save_records(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in records), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="incidentdesk", description="Network incident runbooks and register")
    subs = parser.add_subparsers(dest="action", required=True)
    listing = subs.add_parser("list", help="list scenarios or active incidents")
    listing.add_argument("--incidents", action="store_true")
    show = subs.add_parser("show", help="show a scenario runbook or incident record")
    show.add_argument("id")
    new = subs.add_parser("new", help="open an incident from a scenario")
    new.add_argument("scenario")
    new.add_argument("--title", required=True)
    new.add_argument("--severity", choices=("SEV1", "SEV2", "SEV3", "SEV4"), default="SEV3")
    new.add_argument("--owner", default="unassigned")
    new.add_argument("--note", default="")
    update = subs.add_parser("update", help="change incident status and append a note")
    update.add_argument("id")
    update.add_argument("--status", choices=STATUSES, required=True)
    update.add_argument("--note", required=True)
    report = subs.add_parser("report", help="summarize the incident register")
    report.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        scenarios = load_scenarios()
        scenario_map = {item["id"]: item for item in scenarios}
        path = db_path()
        records = load_records(path)
        if args.action == "list":
            if args.incidents:
                for item in records:
                    print("{} {:<12} {:<5} {}".format(item["id"], item["status"], item["severity"], item["title"]))
            else:
                for item in scenarios:
                    print("{:<9} {}".format(item["id"], item["title"]))
            return 0
        if args.action == "show":
            if args.id in scenario_map:
                print(json.dumps(scenario_map[args.id], indent=2))
            else:
                found = next((item for item in records if item["id"] == args.id), None)
                if found is None:
                    raise ValueError("no scenario or incident named {}".format(args.id))
                print(json.dumps(found, indent=2))
            return 0
        if args.action == "new":
            if args.scenario not in scenario_map:
                raise ValueError("unknown scenario {}; run incidentdesk list".format(args.scenario))
            incident_id = "INC-{}-{}".format(datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"), uuid.uuid4().hex[:6].upper())
            record = {"id": incident_id, "scenario": args.scenario, "title": args.title,
                      "severity": args.severity, "owner": args.owner, "status": "open",
                      "created_at": now(), "updated_at": now(),
                      "notes": ([{"time": now(), "text": args.note}] if args.note else [])}
            records.append(record); save_records(path, records)
            print("Opened {} from {}".format(incident_id, args.scenario)); return 0
        if args.action == "update":
            found = next((item for item in records if item["id"] == args.id), None)
            if found is None:
                raise ValueError("incident {} not found".format(args.id))
            found["status"], found["updated_at"] = args.status, now()
            found.setdefault("notes", []).append({"time": now(), "text": args.note})
            save_records(path, records); print("Updated {} to {}".format(args.id, args.status)); return 0
        totals = {status: sum(1 for item in records if item["status"] == status) for status in STATUSES}
        result = {"generated_at": now(), "total": len(records), "by_status": totals,
                  "by_severity": {sev: sum(1 for item in records if item["severity"] == sev) for sev in ("SEV1", "SEV2", "SEV3", "SEV4")}}
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("Incident report — {} total".format(result["total"]))
            for key, value in totals.items():
                print("  {:<14} {}".format(key, value))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("incidentdesk: {}".format(exc), file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
