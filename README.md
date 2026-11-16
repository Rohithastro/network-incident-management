# Project 3 — Network Troubleshooting and Incident Management

Ten incident runbooks cover DNS failure, DHCP failure, IP conflict, packet loss, high latency, VLAN misconfiguration, routing failure, network outage, TCP connection failure, and firewall blocking traffic. Each includes symptoms, safe fault injection, evidence-first diagnosis, remediation, validation and rollback. A CLI keeps a small JSONL incident register.

## Use the runbooks

Start with an isolated GNS3 lab based on Project 1. Fault injection examples target only that lab; never run them against a production host or network. `tc netem` examples require a Linux endpoint in the simulator. For each exercise, capture the baseline, inject one fault, collect evidence, fix it, verify, then restore the baseline.

## Incident register

Python 3.9+, no third-party dependencies.

```bash
python3 -m venv .venv && . .venv/bin/activate
PYTHONPATH=src python -m incidentdesk list
PYTHONPATH=src python -m incidentdesk show DNS-001
PYTHONPATH=src python -m incidentdesk new DNS-001 --title "Guest clients cannot resolve names" --severity SEV2 --owner "Your Name"
PYTHONPATH=src python -m incidentdesk update INC-20261116123456-ABCDEF --status investigating --note "Gateway responds; DNS query times out"
PYTHONPATH=src python -m incidentdesk report
```

Replace the sample incident ID with the one printed by `new`. Incident records are stored in `incidents.jsonl` in the current directory by default. Set `INCIDENTDESK_FILE` to choose another path. Each record has an ID, scenario, title, severity, owner, status, timestamps, and chronological notes.

## Incident response method

Record impact and scope → gather command output and timestamps → identify the failing layer → state a testable hypothesis → make one controlled change → verify from the affected client and network device → document cause, resolution, and prevention. The runbooks separate fault injection from recovery commands and include rollback guidance.

