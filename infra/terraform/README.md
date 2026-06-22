# Terraform Deployment

This Terraform configuration creates the cloud resources for the Module 7 project:

- 3 EC2 instances, one for each executable.
- 2 SNS topics for message publication.
- 2 SQS queues subscribed to the topics.
- 3 DynamoDB tables.
- 1 ElastiCache Redis node.

It does not create functions, containers, Kubernetes resources, or a service mesh.

## Deploy

Create `terraform.tfvars`:

```hcl
aws_region = "us-east-1"
key_name   = "YOUR_EXISTING_EC2_KEYPAIR"
ssh_cidr   = "YOUR_PUBLIC_IP/32"
api_cidr   = "YOUR_PUBLIC_IP/32"

# Optional. Leave blank if you will copy the repo manually.
app_repo_url = "git@github.com:ArtSabintsev/jhu-module7.git"
app_git_ref  = "main"
```

Then run:

```bash
terraform init
terraform plan -out tfplan
terraform apply tfplan
terraform output
```

If `app_repo_url` is blank, Terraform still creates the cloud infrastructure and writes `/etc/jhu-module7.env` on each VM. Copy the repository to `/opt/jhu-module7`, install it, and enable the matching systemd service.

## Destroy

```bash
terraform destroy
```
