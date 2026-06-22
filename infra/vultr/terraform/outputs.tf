output "api_public_ip" {
  description = "Public IP address of the API VM."
  value       = vultr_instance.service["api"].main_ip
}

output "service_public_ips" {
  description = "Public IP addresses for the three application VMs."
  value       = { for name, instance in vultr_instance.service : name => instance.main_ip }
}

output "kafka_bootstrap_servers" {
  value = "${vultr_database.kafka.host}:${vultr_database.kafka.sasl_port}"
}

output "kafka_topics" {
  value = [
    vultr_database_topic.inventory_updates.name,
    vultr_database_topic.reorder_alerts.name
  ]
}

output "postgres_host" {
  value = vultr_database.postgres.host
}

output "postgres_port" {
  value = vultr_database.postgres.port
}

output "valkey_host" {
  value = vultr_database.valkey.host
}

output "valkey_port" {
  value = vultr_database.valkey.port
}
