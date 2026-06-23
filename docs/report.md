# Project Report

## Project Summary

This project is a distributed cloud application for a candy store inventory reorder workflow. The business process is simple and real: when a product inventory update arrives, the system decides whether the product is low on stock, persists the result, and records a notification audit event for manager follow-up.

The application is distributed because the workflow is split across three independently running executables and four managed cloud services. Each process has a narrow responsibility and communicates through cloud messaging and queueing services instead of direct function calls.

## Business Relevance

Small retail stores can lose sales when popular items run out before staff notice. This system converts an inventory update into an operational reorder signal. It gives the store an auditable record of what was low, when the alert was created, and when the alert was recorded for manager review.

## Architecture

The submitted deployment runs on Vultr. It uses cloud virtual machines for the
three required executables and Vultr managed services for the stateful
components, so the project avoids the prohibited categories: no functions, no
containers, no Kubernetes, and no service mesh.

The Vultr deployment uses:

- `inventory-api` on Vultr Cloud Compute.
- Vultr Managed Kafka for inventory update and reorder alert topics.
- `inventory-worker` on Vultr Cloud Compute.
- Vultr Managed PostgreSQL for inventory, alerts, and notification audit records.
- Vultr Managed Valkey for Redis-compatible API caching.
- `alert-notifier` on Vultr Cloud Compute.

```text
Client
  -> inventory-api VM
  -> Kafka topic: inventory-updates
  -> inventory-worker VM
  -> PostgreSQL inventory + reorder_alerts tables
  -> Valkey cache updates
  -> Kafka topic: reorder-alerts
  -> alert-notifier VM
  -> PostgreSQL notification_audit table
```

## Component Interaction

1. A client sends `POST /inventory` to `inventory-api`.
2. `inventory-api` validates the payload and publishes an `inventory.updated` event to the `inventory-updates` Kafka topic.
3. Kafka retains the event and coordinates delivery to the `inventory-worker` consumer group.
4. `inventory-worker` consumes the event and evaluates the reorder rule.
5. The worker writes current inventory state to Vultr Managed PostgreSQL.
6. The worker updates Valkey-backed cache entries so API reads can avoid repeated database work.
7. If the product is low, the worker creates or updates an open reorder alert in PostgreSQL.
8. The worker publishes a `reorder.alert.opened` event to the `reorder-alerts` Kafka topic.
9. `alert-notifier` consumes that event through its own Kafka consumer group and records a notification audit row in PostgreSQL.
10. `inventory-api` serves `GET /inventory` and `GET /alerts` through Valkey read-through caching backed by PostgreSQL.

## Required Technology Mapping

| Required technology | Cloud service used | How it is used |
| --- | --- | --- |
| Messaging | Vultr Managed Kafka | Publishes inventory update and reorder alert events |
| Queuing | Kafka topics, retention, partitions, and consumer groups | Buffers events for worker and notifier processes |
| Caching | Vultr Managed Valkey | Caches inventory and alert reads for the API |
| Database | Vultr Managed PostgreSQL | Stores inventory, reorder alerts, and notification audit records |

The project uses all four listed technology categories even though the assignment requires only three.

## Three Processes

| Executable | Deployment target | Responsibility |
| --- | --- | --- |
| `inventory-api` | Vultr Cloud Compute VM | HTTP entry point and read API |
| `inventory-worker` | Vultr Cloud Compute VM | Inventory event consumer and reorder evaluator |
| `alert-notifier` | Vultr Cloud Compute VM | Alert event consumer and notification audit recorder |

## Scalability and Efficiency

The API can accept requests quickly because it publishes to Kafka and returns `202 Accepted` instead of doing all work synchronously. Kafka decouples the API from the worker so a burst of inventory updates does not immediately overload the evaluation process. The worker and notifier can be scaled by running additional VM processes in the same Kafka consumer groups. PostgreSQL centralizes durable workflow state in a managed cloud database, while Valkey reduces repeated database reads for common dashboard calls such as inventory lookups and open alerts.

## Cloud Deployment Strategy

The chosen deployment strategy is three Vultr Cloud Compute VMs plus Vultr managed services. This is more operationally explicit than a serverless design, but it matches the assignment restrictions. The application logic runs on VMs, while Vultr manages Kafka, PostgreSQL, and Valkey. That means the project demonstrates cloud integration without hiding the three executables inside prohibited functions or containers.

## Testing and Demonstration

Local automated tests cover the reorder decision rule and message decoding behavior. The cloud demonstration evidence is in `docs/screenshots/` and shows:

- A low-stock `POST /inventory` request returning `202 Accepted`.
- The inventory worker consuming the queued Kafka event.
- A PostgreSQL inventory record.
- A PostgreSQL open alert record.
- The alert notifier recording a notification audit item.
- `GET /alerts` returning the open alert.
- A cached inventory read returning `cache: "HIT"` through Valkey.
- A healthy inventory update resolving the open alert.

## Rubric Alignment

| Rubric criterion | Evidence in this repository |
| --- | --- |
| End-to-end working project | `docs/screenshots/demo-output.txt`, `postgres-evidence.txt`, and the three systemd log files |
| Distributed application | Three separate executables coordinated by Vultr Managed Kafka |
| Cloud integration | `terraform-plan-live-clean.txt`, `terraform-state-list.txt`, and `vultr-resource-list.txt` |
| Technology components | Kafka messaging, Kafka consumer-group queuing, Valkey caching, and PostgreSQL database records |
| Report completeness | This report, `docs/deployment_vultr.md`, and `docs/screenshots/README.md` |
| Source code quality | Python package, clear modules, tests, explicit environment config |
| Real-world relevance | Retail inventory reorder workflow |

## Limitations

The notification process records an audit event instead of sending email or SMS. That is deliberate: adding an email or SMS provider would introduce another application component outside the assignment's allowed set. The audit table still proves that the alert event moved through the distributed workflow.
