# Project Report

## Summary

This project is a live distributed cloud application for a candy-store inventory reorder workflow.

The store has a simple problem: low-stock products get missed until a customer wants something that is no longer on the shelf. This system turns each inventory update into a decision the store can act on. If the product is below its reorder threshold, the system opens a reorder alert and records a manager notification audit. If stock recovers, the system resolves the alert.

The work is split across three executables on three Vultr Cloud Compute VMs. Kafka coordinates the event flow. PostgreSQL stores durable records. Valkey handles cache reads. Vultr manages those services.

## Architecture

```text
Client
  -> inventory-api VM
  -> Kafka topic: inventory-updates
  -> inventory-worker VM
  -> PostgreSQL inventory + reorder_alerts tables
  -> Valkey cache
  -> Kafka topic: reorder-alerts
  -> alert-notifier VM
  -> PostgreSQL notification_audit table
```

## Three Processes

| Executable | Runs on | Job |
| --- | --- | --- |
| `inventory-api` | `jhu-module7-api` | Accepts inventory updates, publishes events, and serves read endpoints |
| `inventory-worker` | `jhu-module7-worker` | Consumes inventory events, applies reorder logic, writes records, and publishes alert events |
| `alert-notifier` | `jhu-module7-notifier` | Consumes alert events and records notification audit rows |

## Technology Components

| Required category | Live cloud service | How it is used |
| --- | --- | --- |
| Messaging | Vultr Managed Kafka | Carries inventory update and reorder alert events |
| Queuing | Kafka topics and consumer groups | Buffers work and assigns events to worker processes |
| Caching | Vultr Managed Valkey | Caches inventory reads for the API |
| Database | Vultr Managed PostgreSQL | Stores inventory rows, reorder alerts, and notification audit rows |

The assignment requires at least three of these categories. The live deployment uses all four.

## Component Interaction

1. A client sends `POST /inventory` to `inventory-api`.
2. The API validates the payload and publishes `inventory.updated` to `inventory-updates`.
3. Kafka holds the event until `inventory-worker` consumes it.
4. The worker evaluates the reorder rule.
5. The worker writes the current inventory state to PostgreSQL.
6. The worker updates Valkey cache entries for fast API reads.
7. If the product is low, the worker opens a reorder alert in PostgreSQL.
8. The worker publishes `reorder.alert.opened` to `reorder-alerts`.
9. `alert-notifier` consumes the alert event.
10. The notifier writes a notification audit row to PostgreSQL.
11. A later healthy inventory update resolves the open alert.

## Scalability and Efficiency

The API returns `202 Accepted` after publishing to Kafka. It does not wait for the whole reorder workflow to finish. That keeps the request path short.

Kafka gives the worker and notifier room to lag during a burst instead of dropping work. More worker or notifier processes can join the same consumer groups if event volume grows. PostgreSQL keeps the record of truth in one managed database. Valkey cuts repeated database reads for common inventory lookups.

## Evidence

The evidence package is in `docs/screenshots/`.

| Rubric item | Evidence |
| --- | --- |
| End-to-end working project | `demo-output.txt`, `postgres-evidence.txt`, service logs |
| Distributed application | `01-vultr-three-instances.png`, systemd logs |
| Cloud integration | `02-vultr-managed-databases.png`, `terraform-plan-live-clean.txt` |
| Technology components | `03-vultr-kafka-topics.png`, `valkey-evidence.txt`, `postgres-evidence.txt` |
| Report completeness | This report and `docs/deployment_vultr.md` |
| Source code quality | Python package, tests, clear modules, environment-driven config |
| Real-world relevance | Candy-store reorder workflow with alert and notification audit records |

## Demonstrated Result

The live demo used `GUMMY-001`.

First, the API accepted a quantity of `8` with a reorder threshold of `10`. The worker marked the product as `REORDER_NEEDED`, opened an alert, and the notifier recorded the manager audit row.

Then the API accepted a quantity of `40`. The worker marked the inventory as `HEALTHY` and resolved the open alert.

The final PostgreSQL evidence shows:

- inventory row: `HEALTHY`
- reorder alert: `RESOLVED`
- notification audit: `RECORDED`

That is the business process from start to finish.
