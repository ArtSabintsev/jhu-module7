# Vultr Terraform Deployment

This deployment uses only resources allowed by the assignment:

- Three Vultr Cloud Compute VMs for the three executables.
- Vultr Managed Apache Kafka for messaging and queue-like event buffering.
- Vultr Managed PostgreSQL for durable application state.
- Vultr Managed Valkey for Redis-compatible caching.

It does not create functions, containers, Kubernetes, or a service mesh.

## Prerequisites

1. Export a Vultr API key:

```bash
export VULTR_API_KEY="..."
```

2. Create or identify Vultr SSH key IDs:

```bash
vultr-cli ssh-key list
```

3. List managed database plans for PostgreSQL, Kafka, and Valkey:

```bash
vultr-cli database plan list
```

The exact plan IDs vary by region and change over time, so the Terraform variables require explicit plan IDs.

## terraform.tfvars

```hcl
vultr_region = "ewr"
ssh_cidr     = "YOUR_PUBLIC_IP/32"
api_cidr     = "YOUR_PUBLIC_IP/32"
ssh_key_ids  = ["YOUR_VULTR_SSH_KEY_ID"]
trusted_ips  = ["YOUR_PUBLIC_IP/32"]

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

For a private GitHub repo, the VM must be able to clone over SSH. The simplest automated approach is to add a read-only deploy key for this repository before applying Terraform and pass that private key as `github_deploy_key_private`. This stores the key in Terraform state, so use it only for class/demo infrastructure. If you do not want that, copy the repo manually after the VMs exist.

For `trusted_ips`, a tightly locked deployment needs the app VM IPs, which are not known until after creation. For a short class demo, `["0.0.0.0/0"]` is the simplest working value because PostgreSQL, Kafka, and Valkey still require credentials and TLS-capable clients.

## Deploy

```bash
terraform init
terraform plan -out tfplan
terraform apply tfplan
terraform output
```

## Verify

```bash
curl -sS http://$(terraform output -raw api_public_ip):8000/health
```

Then run the API demo from the root README.

## Destroy

```bash
terraform destroy
```
