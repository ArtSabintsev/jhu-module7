# Vultr Terraform Stack

This Terraform stack defines the submitted Module 7 deployment on Vultr.

## Managed Resources

| Terraform resource | Purpose |
| --- | --- |
| `vultr_instance.service["api"]` | Runs `inventory-api` |
| `vultr_instance.service["worker"]` | Runs `inventory-worker` |
| `vultr_instance.service["notifier"]` | Runs `alert-notifier` |
| `vultr_database.postgres` | Managed PostgreSQL database |
| `vultr_database.kafka` | Managed Apache Kafka cluster |
| `vultr_database.valkey` | Managed Valkey cache |
| `vultr_database_topic.inventory_updates` | Kafka `inventory-updates` topic |
| `vultr_database_topic.reorder_alerts` | Kafka `reorder-alerts` topic |
| `vultr_firewall_group.app` | Application firewall |
| `vultr_firewall_rule.ssh` | SSH access from the trusted IP |
| `vultr_firewall_rule.api` | API access from the trusted IP |

## Runtime Values

| Output | Value |
| --- | --- |
| `api_public_ip` | `API_PUBLIC_IP` |
| `service_public_ips.api` | `API_PUBLIC_IP` |
| `service_public_ips.worker` | `WORKER_PUBLIC_IP` |
| `service_public_ips.notifier` | `NOTIFIER_PUBLIC_IP` |
| `kafka_topics` | `inventory-updates`, `reorder-alerts` |

The submitted output is captured in `docs/screenshots/terraform-output.txt` with public infrastructure values redacted.

## Validation

The submitted stack was validated with:

```bash
terraform fmt -check
terraform validate
terraform plan -no-color
```

The final plan reported:

```text
No changes. Your infrastructure matches the configuration.
```

## Teardown

Destroy the Vultr resources after submission review:

```bash
cd infra/vultr/terraform
source ~/.zshrc >/dev/null 2>&1
terraform destroy
```
