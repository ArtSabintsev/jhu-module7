# JHU Module 7 - Distributed Cloud Inventory Reorder

This public repository contains the source code, deployment configuration, and captured evidence for a Vultr deployment of a candy-store inventory reorder system for JHU Module 7.

The system does one business job: it accepts an inventory update, decides whether the product needs reorder attention, records the result, and records a manager notification audit. The submitted deployment split the work across three long-running executables on three cloud VMs. State and coordination were provided by managed Vultr services.

## Deployment Architecture

```text
Client
  -> inventory-api on Vultr Cloud Compute
  -> Kafka topic: inventory-updates
  -> inventory-worker on Vultr Cloud Compute
  -> Vultr Managed PostgreSQL
  -> Vultr Managed Valkey
  -> Kafka topic: reorder-alerts
  -> alert-notifier on Vultr Cloud Compute
  -> PostgreSQL notification_audit table
```

## Business Process

A store sends a product inventory update to the API.

```text
If quantity <= reorder_threshold:
  open or update a reorder alert
  publish an alert event
  record a manager notification audit

If quantity > reorder_threshold:
  mark any open alert for that SKU as resolved
```

The demo SKU is `GUMMY-001`, Sour Gummy Worms.

## Required Components

| Assignment requirement | Submitted implementation |
| --- | --- |
| Three executables | `inventory-api`, `inventory-worker`, `alert-notifier` |
| Messaging | Vultr Managed Kafka topics |
| Queuing | Kafka partitions, retention, and consumer groups |
| Caching | Vultr Managed Valkey |
| Database | Vultr Managed PostgreSQL |
| Cloud deployment | Three Vultr Cloud Compute VMs plus Vultr managed services |

The assignment requires three of the four technology categories. This implementation uses all four.

## Executables

`inventory-api`
: Public HTTP service. It accepts `POST /inventory`, publishes inventory events, and serves inventory and alert reads through Valkey-backed caching.

`inventory-worker`
: Kafka consumer for `inventory-updates`. It applies the reorder rule, writes inventory and alert records to PostgreSQL, updates cache entries, and publishes alert events.

`alert-notifier`
: Kafka consumer for `reorder-alerts`. It records manager notification audit rows in PostgreSQL.

## Evidence

The working evidence is in [docs/screenshots](docs/screenshots).

Key files:

- `01-vultr-three-instances.png`
- `02-vultr-managed-databases.png`
- `03-vultr-kafka-topics.png`
- `demo-output.txt`
- `postgres-evidence.txt`
- `valkey-evidence.txt`
- `kafka-topics.txt`
- `terraform-plan-clean.txt`
- `03-systemctl-api.txt`
- `04-systemctl-worker.txt`
- `05-systemctl-notifier.txt`

The evidence shows the full path: low-stock inventory update, Kafka event processing, PostgreSQL records, Valkey cache hit, notification audit, and final alert resolution.

## Runbook

Submitted deployment details are in [docs/deployment_vultr.md](docs/deployment_vultr.md).

Terraform details are in [infra/vultr/terraform](infra/vultr/terraform).

The primary submitted path is Vultr. An earlier AWS-compatible backend variant is also present and selected with `APP_BACKEND=aws`; the public evidence and runbook focus on the Vultr deployment.

## Local Checks

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

The submitted evidence includes `pytest-output.txt` with `11 passed`.

## Credential Safety

Only example configuration files are tracked. Real `.env` files, Terraform variable files, Terraform state, local virtual environments, generated packages, logs, and cloud credentials are ignored.

## Public Repository

Canonical GitHub URL: https://github.com/ArtSabintsev/jhu-module7-distributed-cloud-inventory-reorder
