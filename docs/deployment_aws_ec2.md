# AWS EC2 Deployment Guide

## Why This Deployment Fits the Assignment

This project uses EC2 virtual machines for execution and managed AWS services for messaging, queuing, caching, and database storage. It avoids the prohibited categories: no functions, no containers, no Kubernetes, and no service mesh.

## Cloud Resources

| Resource | Purpose |
| --- | --- |
| EC2 API instance | Runs `inventory-api` |
| EC2 worker instance | Runs `inventory-worker` |
| EC2 notifier instance | Runs `alert-notifier` |
| SNS inventory topic | Messaging path for inventory updates |
| SQS inventory queue | Queue consumed by `inventory-worker` |
| SNS alert topic | Messaging path for reorder alerts |
| SQS alert queue | Queue consumed by `alert-notifier` |
| DynamoDB inventory table | Stores current product state |
| DynamoDB alerts table | Stores open and resolved reorder alerts |
| DynamoDB notification table | Stores notification audit events |
| ElastiCache Redis | Caches read results for inventory and alerts |

## Deployment Steps

1. Create or choose an EC2 key pair in AWS.
2. Determine your public IP address and use `/32` CIDR notation for `ssh_cidr` and `api_cidr`.
3. From `infra/terraform`, create `terraform.tfvars`.
4. Run `terraform init`, `terraform plan -out tfplan`, and `terraform apply tfplan`.
5. Confirm Terraform outputs include the API public IP, queue URLs, topic ARNs, table names, and Redis URL.
6. If `app_repo_url` was not set, copy this repository to `/opt/jhu-module7` on each VM.
7. Install the Python package on each VM:

```bash
cd /opt/jhu-module7
python3.11 -m venv .venv
.venv/bin/pip install -e .
```

8. Copy the correct service file from `deploy/systemd` to `/etc/systemd/system` on each VM.
9. Start each service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now inventory-api
sudo systemctl enable --now inventory-worker
sudo systemctl enable --now alert-notifier
```

10. Verify service status:

```bash
systemctl status inventory-api --no-pager
systemctl status inventory-worker --no-pager
systemctl status alert-notifier --no-pager
```

## End-to-End Test

Replace `EC2_API_PUBLIC_IP` with the Terraform output.

```bash
curl -sS -X POST http://EC2_API_PUBLIC_IP:8000/inventory \
  -H 'content-type: application/json' \
  -d '{"sku":"GUMMY-001","name":"Sour Gummy Worms","quantity":8,"reorder_threshold":10,"vendor":"Acme Candy Supply"}' | jq
```

Wait a few seconds for SNS, SQS, and the worker process.

```bash
curl -sS http://EC2_API_PUBLIC_IP:8000/inventory/GUMMY-001 | jq
curl -sS http://EC2_API_PUBLIC_IP:8000/alerts | jq
```

The first `GET` should show `cache: "MISS"`. A repeated call should show `cache: "HIT"` if Redis is reachable.

## Evidence to Capture

Capture screenshots of the AWS console and terminal output listed in [screenshots/README.md](screenshots/README.md). The screenshots are not optional; the rubric makes working evidence a major part of the grade.
