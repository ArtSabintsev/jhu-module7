# Screenshot Checklist

Screenshots should prove the project works end to end. Put final images in this directory before submission.

## Required Screenshots

1. GitHub repository showing source files and documentation.
2. Cloud VM page showing the three VMs: API, worker, and notifier.
3. Terminal or cloud console showing `inventory-api` service running.
4. Terminal or cloud console showing `inventory-worker` service running.
5. Terminal or cloud console showing `alert-notifier` service running.
6. Messaging page showing the inventory update topic and reorder alert topic.
7. Queueing evidence: SQS queues on AWS, or Kafka topics/consumer groups on Vultr.
8. Database page showing inventory, reorder alerts, and notification audit tables.
9. Cache page showing the Redis or Valkey endpoint.
10. Terminal screenshot of `POST /inventory` returning `202 Accepted`.
11. Database inventory row/item for the submitted SKU.
12. Database reorder alert row/item for the low-stock SKU.
13. Database notification audit row/item created by `alert-notifier`.
14. Terminal screenshot of `GET /alerts` showing the open alert.
15. Terminal or API output showing a repeated `GET` call with `cache: "HIT"`.

## Suggested File Names

```text
01-github-repo.png
02-cloud-three-instances.png
03-systemctl-api.png
04-systemctl-worker.png
05-systemctl-notifier.png
06-messaging-topics.png
07-queue-evidence.png
08-database-tables.png
09-cache-endpoint.png
10-post-inventory.png
11-database-inventory-item.png
12-database-alert-item.png
13-database-notification-item.png
14-get-alerts.png
15-cache-hit.png
```
