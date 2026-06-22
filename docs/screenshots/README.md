# Screenshot Checklist

Screenshots should prove the project works end to end. Put final images in this directory before submission.

## Required Screenshots

1. GitHub repository showing source files and documentation.
2. EC2 instances page showing the three VMs: API, worker, and notifier.
3. Terminal or AWS console showing `inventory-api` service running.
4. Terminal or AWS console showing `inventory-worker` service running.
5. Terminal or AWS console showing `alert-notifier` service running.
6. SNS topics page showing the inventory update topic and reorder alert topic.
7. SQS queues page showing the inventory worker queue and alert notifier queue.
8. DynamoDB tables page showing inventory, reorder alerts, and notification audit tables.
9. ElastiCache Redis page showing the cache endpoint.
10. Terminal screenshot of `POST /inventory` returning `202 Accepted`.
11. DynamoDB inventory table item for the submitted SKU.
12. DynamoDB reorder alert item for the low-stock SKU.
13. DynamoDB notification audit item created by `alert-notifier`.
14. Terminal screenshot of `GET /alerts` showing the open alert.
15. Terminal or API output showing a repeated `GET` call with `cache: "HIT"`.

## Suggested File Names

```text
01-github-repo.png
02-ec2-three-instances.png
03-systemctl-api.png
04-systemctl-worker.png
05-systemctl-notifier.png
06-sns-topics.png
07-sqs-queues.png
08-dynamodb-tables.png
09-elasticache-redis.png
10-post-inventory.png
11-dynamodb-inventory-item.png
12-dynamodb-alert-item.png
13-dynamodb-notification-item.png
14-get-alerts.png
15-cache-hit.png
```
