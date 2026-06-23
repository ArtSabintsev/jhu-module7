# Vultr Terraform Stack

This Terraform stack defines the live Module 7 deployment on Vultr.

## Managed Resources

| Terraform resource | Live purpose |
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
| `api_public_ip` | `66.135.2.150` |
| `service_public_ips.api` | `66.135.2.150` |
| `service_public_ips.worker` | `45.63.17.131` |
| `service_public_ips.notifier` | `108.61.23.88` |
| `kafka_topics` | `inventory-updates`, `reorder-alerts` |

The live output is captured in `docs/screenshots/terraform-output.txt`.

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

Destroy the live Vultr resources after submission review:

```bash
cd infra/vultr/terraform
source ~/.zshrc >/dev/null 2>&1
terraform destroy
```
