# Vultr Deployment

This is the deployment submitted for Module 7.

## Topology

| Role | Vultr resource | Purpose |
| --- | --- | --- |
| API process | `jhu-module7-api` VM | Accepts inventory updates and serves API reads |
| Worker process | `jhu-module7-worker` VM | Consumes inventory events and applies reorder logic |
| Notifier process | `jhu-module7-notifier` VM | Consumes alert events and records notification audits |
| Messaging | `jhu-module7-kafka` | Publishes inventory and alert events |
| Queuing | Kafka topics and consumer groups | Buffers work for the worker and notifier |
| Cache | `jhu-module7-valkey` | Stores API read-through cache entries |
| Database | `jhu-module7-postgres` | Stores inventory, reorder alerts, and notification audit rows |

## Submitted Endpoint Pattern

| Service | Endpoint |
| --- | --- |
| API | `http://API_PUBLIC_IP:8000` |
| Health check | `http://API_PUBLIC_IP:8000/health` |

The submitted evidence redacts public infrastructure addresses and managed-service hostnames. The original grader-facing run used the same endpoints shown in the captured command output shape.

## Kafka Topics

| Topic | Used by | Evidence |
| --- | --- | --- |
| `inventory-updates` | API publishes, worker consumes | `docs/screenshots/03-vultr-kafka-topics.png` |
| `reorder-alerts` | Worker publishes, notifier consumes | `docs/screenshots/03-vultr-kafka-topics.png` |

## Workflow

1. `inventory-api` receives a low-stock `POST /inventory` request.
2. The API publishes an `inventory.updated` event to Kafka.
3. `inventory-worker` consumes that event from the `inventory-worker` consumer group.
4. The worker writes the inventory row to PostgreSQL.
5. The worker opens a reorder alert in PostgreSQL when quantity is below threshold.
6. The worker publishes a `reorder.alert.opened` event to Kafka.
7. `alert-notifier` consumes the alert event from the `alert-notifier` consumer group.
8. The notifier writes a notification audit row to PostgreSQL.
9. The API serves repeated inventory reads from Valkey-backed cache.
10. A healthy inventory update resolves the open alert.

## Evidence Map

| Claim | Evidence file |
| --- | --- |
| Three cloud VMs are running | `01-vultr-three-instances.png` |
| Managed Postgres, Kafka, and Valkey are running | `02-vultr-managed-databases.png` |
| Kafka topics exist | `03-vultr-kafka-topics.png`, `kafka-topics.txt` |
| API is public and healthy | `health-output.txt` |
| End-to-end workflow works | `demo-output.txt` |
| PostgreSQL stores the records | `postgres-evidence.txt` |
| Valkey cache works | `valkey-evidence.txt`, `demo-output.txt` |
| Three services are active | `03-systemctl-api.txt`, `04-systemctl-worker.txt`, `05-systemctl-notifier.txt` |
| Terraform matches the submitted stack | `terraform-plan-clean.txt`, `terraform-state-list.txt` |

## Teardown

The cloud resources are billable. After grading evidence is captured, destroy the stack from the Terraform directory:

```bash
cd infra/vultr/terraform
source ~/.zshrc >/dev/null 2>&1
terraform destroy
```
