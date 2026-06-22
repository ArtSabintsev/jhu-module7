output "api_public_ip" {
  description = "Public IP address of the API EC2 instance."
  value       = aws_instance.service["api"].public_ip
}

output "service_public_ips" {
  description = "Public IP addresses for all three EC2 instances."
  value       = { for name, instance in aws_instance.service : name => instance.public_ip }
}

output "inventory_topic_arn" {
  value = aws_sns_topic.inventory_updates.arn
}

output "alert_topic_arn" {
  value = aws_sns_topic.reorder_alerts.arn
}

output "inventory_queue_url" {
  value = aws_sqs_queue.inventory_worker.id
}

output "alert_queue_url" {
  value = aws_sqs_queue.alert_notifier.id
}

output "dynamodb_tables" {
  value = {
    inventory     = aws_dynamodb_table.inventory.name
    alerts        = aws_dynamodb_table.alerts.name
    notifications = aws_dynamodb_table.notifications.name
  }
}

output "redis_url" {
  value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0"
}
