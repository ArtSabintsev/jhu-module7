# Vultr Deployment Guide

## Why Vultr Fits the Assignment

Vultr is acceptable for this project if the application uses Vultr managed services instead of self-installed databases, caches, or message brokers. This deployment uses:

| Requirement | Vultr service |
| --- | --- |
| Three executables | Three Vultr Cloud Compute VMs |
| Messaging | Vultr Managed Apache Kafka |
| Queuing | Kafka topics, retention, partitions, and consumer groups |
| Caching | Vultr Managed Valkey, Redis-compatible |
| Database | Vultr Managed PostgreSQL |

This still avoids functions, containers, Kubernetes, and service mesh.

## Architecture

```text
Client
  -> inventory-api on Vultr Cloud Compute
  -> Vultr Managed Kafka topic: inventory-updates
  -> inventory-worker on Vultr Cloud Compute
  -> Vultr Managed PostgreSQL
  -> Vultr Managed Valkey
  -> Vultr Managed Kafka topic: reorder-alerts
  -> alert-notifier on Vultr Cloud Compute
  -> PostgreSQL notification_audit table
```

## Deployment Steps

1. Export your Vultr API key:

```bash
export VULTR_API_KEY="..."
```

2. Create a deploy key for the private GitHub repo or plan to copy the repo manually. Full cloud-init bootstrap requires `github_deploy_key_private` in Terraform.

3. Find Vultr region, OS, SSH key, and managed database plan IDs:

```bash
vultr-cli regions list
vultr-cli os list
vultr-cli ssh-key list
vultr-cli database plan list
```

4. Create `infra/vultr/terraform/terraform.tfvars`:

```hcl
vultr_region = "ewr"
ssh_cidr     = "YOUR_PUBLIC_IP/32"
api_cidr     = "YOUR_PUBLIC_IP/32"
ssh_key_ids  = ["YOUR_VULTR_SSH_KEY_ID"]

# For a simple class demo, this can be ["0.0.0.0/0"].
# A tighter deployment should restrict this to known client/VM IPs.
trusted_ips = ["0.0.0.0/0"]

postgres_plan = "replace-with-postgres-plan-id"
kafka_plan    = "replace-with-kafka-plan-id"
valkey_plan   = "replace-with-valkey-plan-id"

app_repo_url = "git@github.com:ArtSabintsev/jhu-module7.git"
app_git_ref  = "main"

github_deploy_key_private = <<EOT
-----BEGIN OPENSSH PRIVATE KEY-----
replace-with-read-only-github-deploy-key
-----END OPENSSH PRIVATE KEY-----
EOT
```

5. Apply Terraform:

```bash
cd infra/vultr/terraform
terraform init
terraform plan -out tfplan
terraform apply tfplan
terraform output
```

6. Confirm the services are running:

```bash
ssh linuxuser@$(terraform output -raw api_public_ip) 'systemctl status inventory-api --no-pager'
```

Use the worker and notifier IPs from `terraform output service_public_ips` for the other two services.

## End-to-End Test

```bash
API_BASE_URL="http://$(terraform output -raw api_public_ip):8000" ../../../scripts/demo_requests.sh
```

The first read should show `cache: "MISS"` and a repeated read should show `cache: "HIT"` if Valkey is reachable.

## Manual Fallback

If you do not want to put a deploy key into Terraform state, leave `github_deploy_key_private` empty, let Terraform create the infrastructure, then copy the repo to `/opt/jhu-module7` on each VM and run:

```bash
cd /opt/jhu-module7
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/vultr-init-db
.venv/bin/vultr-init-kafka
sudo systemctl daemon-reload
sudo systemctl enable --now SERVICE_NAME
```

Use only the correct service per VM: `inventory-api` on the API VM, `inventory-worker` on the worker VM, and `alert-notifier` on the notifier VM.
