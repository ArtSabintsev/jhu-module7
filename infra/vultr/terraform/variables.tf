variable "vultr_region" {
  description = "Vultr region code, for example ewr, ord, atl, dfw, lhr."
  type        = string
  default     = "ewr"
}

variable "project_name" {
  description = "Prefix for all named Vultr resources."
  type        = string
  default     = "jhu-module7"
}

variable "ssh_cidr" {
  description = "CIDR block allowed to SSH to the application instances."
  type        = string
}

variable "api_cidr" {
  description = "CIDR block allowed to call the API service."
  type        = string
}

variable "ssh_key_ids" {
  description = "Existing Vultr SSH key IDs to install on the instances."
  type        = list(string)
}

variable "instance_plan" {
  description = "Vultr Cloud Compute plan for each application VM."
  type        = string
  default     = "vc2-1c-1gb"
}

variable "os_id" {
  description = "Vultr OS ID for Ubuntu 24.04 x64. Confirm with `vultr-cli os list`."
  type        = number
  default     = 2284
}

variable "postgres_plan" {
  description = "Managed PostgreSQL plan ID. Confirm available plans with the Vultr API or CLI."
  type        = string
}

variable "kafka_plan" {
  description = "Managed Apache Kafka plan ID. Confirm available plans with the Vultr API or CLI."
  type        = string
}

variable "valkey_plan" {
  description = "Managed Valkey plan ID. Confirm available plans with the Vultr API or CLI."
  type        = string
}

variable "trusted_ips" {
  description = "Trusted public IP addresses allowed to reach managed databases."
  type        = list(string)
}

variable "kafka_topic_partitions" {
  description = "Kafka partitions for each project topic."
  type        = number
  default     = 3
}

variable "kafka_topic_replication" {
  description = "Kafka replication factor for each project topic."
  type        = number
  default     = 1
}

variable "kafka_topic_retention_hours" {
  description = "Kafka retention hours for each project topic."
  type        = number
  default     = 120
}

variable "app_repo_url" {
  description = "Git URL to clone on each VM. HTTPS works for public repos; SSH requires github_deploy_key_private."
  type        = string
  default     = "https://github.com/ArtSabintsev/jhu-module7-distributed-cloud-inventory-reorder.git"
}

variable "app_git_ref" {
  description = "Git branch, tag, or commit to check out."
  type        = string
  default     = "main"
}

variable "github_deploy_key_private" {
  description = "Optional private deploy key for SSH-only clone workflows. This is written to cloud-init and Terraform state; use only for class/demo infrastructure."
  type        = string
  default     = ""
  sensitive   = true
}
