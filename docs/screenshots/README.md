# Evidence Package

This directory contains the evidence for the live Vultr deployment verified on 2026-06-23.

## Portal Screenshots

```text
01-vultr-three-instances.png       Three Vultr VMs running the three executables
02-vultr-managed-databases.png     Managed PostgreSQL, Kafka, and Valkey running
03-vultr-kafka-topics.png          Kafka topics: inventory-updates and reorder-alerts
```

## Runtime Evidence

```text
03-systemctl-api.txt               inventory-api service status and logs
04-systemctl-worker.txt            inventory-worker service status and logs
05-systemctl-notifier.txt          alert-notifier service status and logs
health-output.txt                  Public API health check
demo-output.txt                    End-to-end API demo against the public API
postgres-evidence.txt              Inventory, alert, and notification audit rows
valkey-evidence.txt                Direct Valkey ping and cached key evidence
kafka-topics.txt                   Kafka topic configuration
firewall-rules.txt                 API and SSH firewall rules
pytest-output.txt                  Local test output
```

## Terraform Evidence

```text
terraform-output.txt               Service IPs and managed-service endpoints
terraform-state-list.txt           Terraform-managed resource list
terraform-plan-live-clean.txt      Final no-change Terraform plan
vultr-resource-list.txt            Sanitized Vultr resource list
```

## How To Read The Proof

Start with the three screenshots. They prove the cloud resources exist and are running.

Then read `demo-output.txt` and `postgres-evidence.txt`. Those two files prove the business workflow: low inventory opens an alert, the notifier records it, and a healthy update resolves it.

The service logs prove the three executables were running independently on cloud VMs while the demo ran.
