terraform {
  required_version = ">= 1.6.0"

  required_providers {
    vultr = {
      source  = "vultr/vultr"
      version = "~> 2.31"
    }
  }
}

provider "vultr" {}

locals {
  ssh_cidr_parts = split("/", var.ssh_cidr)
  api_cidr_parts = split("/", var.api_cidr)

  services = {
    api = {
      executable = "inventory-api"
    }
    worker = {
      executable = "inventory-worker"
    }
    notifier = {
      executable = "alert-notifier"
    }
  }

  tags = ["jhu-module7", "distributed-app"]
}

resource "vultr_firewall_group" "app" {
  description = "${var.project_name} application firewall"
}

resource "vultr_firewall_rule" "ssh" {
  firewall_group_id = vultr_firewall_group.app.id
  protocol          = "tcp"
  ip_type           = "v4"
  subnet            = local.ssh_cidr_parts[0]
  subnet_size       = tonumber(local.ssh_cidr_parts[1])
  port              = "22"
  notes             = "SSH from trusted IP"
}

resource "vultr_firewall_rule" "api" {
  firewall_group_id = vultr_firewall_group.app.id
  protocol          = "tcp"
  ip_type           = "v4"
  subnet            = local.api_cidr_parts[0]
  subnet_size       = tonumber(local.api_cidr_parts[1])
  port              = "8000"
  notes             = "Inventory API"
}

resource "vultr_database" "postgres" {
  database_engine         = "pg"
  database_engine_version = "16"
  region                  = var.vultr_region
  plan                    = var.postgres_plan
  label                   = "${var.project_name}-postgres"
  trusted_ips             = var.trusted_ips
}

resource "vultr_database" "kafka" {
  database_engine         = "kafka"
  database_engine_version = "3.8"
  region                  = var.vultr_region
  plan                    = var.kafka_plan
  label                   = "${var.project_name}-kafka"
  trusted_ips             = var.trusted_ips
}

resource "vultr_database" "valkey" {
  database_engine         = "valkey"
  database_engine_version = "8.1"
  region                  = var.vultr_region
  plan                    = var.valkey_plan
  label                   = "${var.project_name}-valkey"
  trusted_ips             = var.trusted_ips
}

resource "vultr_database_topic" "inventory_updates" {
  database_id     = vultr_database.kafka.id
  name            = "inventory-updates"
  partitions      = tostring(var.kafka_topic_partitions)
  replication     = tostring(var.kafka_topic_replication)
  retention_hours = tostring(var.kafka_topic_retention_hours)
  retention_bytes = "-1"
}

resource "vultr_database_topic" "reorder_alerts" {
  database_id     = vultr_database.kafka.id
  name            = "reorder-alerts"
  partitions      = tostring(var.kafka_topic_partitions)
  replication     = tostring(var.kafka_topic_replication)
  retention_hours = tostring(var.kafka_topic_retention_hours)
  retention_bytes = "-1"
}

resource "vultr_instance" "service" {
  for_each = local.services

  label             = "${var.project_name}-${each.key}"
  hostname          = "${var.project_name}-${each.key}"
  region            = var.vultr_region
  plan              = var.instance_plan
  os_id             = var.os_id
  ssh_key_ids       = var.ssh_key_ids
  firewall_group_id = vultr_firewall_group.app.id
  user_scheme       = "limited"
  tags              = local.tags

  user_data = templatefile("${path.module}/cloud-init.yaml.tftpl", {
    app_git_ref               = var.app_git_ref
    app_repo_url              = var.app_repo_url
    executable                = each.value.executable
    github_deploy_key_private = var.github_deploy_key_private
    kafka_host                = vultr_database.kafka.host
    kafka_sasl_port           = vultr_database.kafka.sasl_port
    kafka_ca_certificate      = vultr_database.kafka.ca_certificate
    kafka_user                = vultr_database.kafka.user
    kafka_password            = vultr_database.kafka.password
    postgres_host             = vultr_database.postgres.host
    postgres_port             = vultr_database.postgres.port
    postgres_user             = vultr_database.postgres.user
    postgres_password         = vultr_database.postgres.password
    postgres_dbname           = vultr_database.postgres.dbname
    valkey_host               = vultr_database.valkey.host
    valkey_port               = vultr_database.valkey.port
    valkey_password           = vultr_database.valkey.password
    kafka_topic_replication   = var.kafka_topic_replication
  })

  depends_on = [
    vultr_database.postgres,
    vultr_database.kafka,
    vultr_database.valkey,
    vultr_database_topic.inventory_updates,
    vultr_database_topic.reorder_alerts
  ]

  lifecycle {
    ignore_changes = [user_data]
  }
}
