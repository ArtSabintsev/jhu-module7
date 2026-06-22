# Project Report

## Project Summary

This project is a distributed cloud application for a candy store inventory reorder workflow. The business process is simple and real: when a product inventory update arrives, the system decides whether the product is low on stock, persists the result, and records a notification audit event for manager follow-up.

The application is distributed because the workflow is split across three independently running executables and four managed cloud services. Each process has a narrow responsibility and communicates through cloud messaging and queueing services instead of direct function calls.

## Business Relevance

Small retail stores can lose sales when popular items run out before staff notice. This system converts an inventory update into an operational reorder signal. It gives the store an auditable record of what was low, when the alert was created, and when the alert was recorded for manager review.

## Architecture

The deployed system can use either AWS or Vultr. The Vultr deployment is the preferred non-AWS path because Vultr offers managed Kafka, PostgreSQL, and Valkey.

The AWS deployment uses:

- `inventory-api` on EC2 to accept inventory updates and serve read endpoints.
- Amazon SNS to publish inventory and alert events.
- Amazon SQS to buffer work for background processes.
- `inventory-worker` on EC2 to apply reorder logic and persist state.
- DynamoDB to store inventory, alerts, and notification audit records.
- ElastiCache Redis to cache inventory and alert reads.
- `alert-notifier` on EC2 to consume alert events and record notification audits.

The Vultr deployment uses:

- `inventory-api` on Vultr Cloud Compute.
- Vultr Managed Kafka for inventory update and reorder alert topics.
- `inventory-worker` on Vultr Cloud Compute.
- Vultr Managed PostgreSQL for inventory, alerts, and notification audit records.
- Vultr Managed Valkey for Redis-compatible API caching.
- `alert-notifier` on Vultr Cloud Compute.

## Component Interaction

1. A client sends `POST /inventory` to `inventory-api`.
2. `inventory-api` validates the payload and publishes an `inventory.updated` event to SNS.
3. SNS delivers the event to an SQS queue.
4. `inventory-worker` long-polls the queue and evaluates the reorder rule.
5. The worker writes current inventory state to DynamoDB.
6. If the product is low, the worker creates or updates an open reorder alert in DynamoDB.
7. The worker publishes a `reorder.alert.opened` event to SNS.
8. SNS delivers that alert event to a second SQS queue.
9. `alert-notifier` consumes the alert event and records a notification audit item in DynamoDB.
10. `inventory-api` serves `GET /inventory` and `GET /alerts` through Redis read-through caching backed by DynamoDB.

## Required Technology Mapping

| Required technology | Cloud service used | How it is used |
| --- | --- | --- |
| Messaging | Amazon SNS or Vultr Managed Kafka | Publishes inventory update and reorder alert events |
| Queuing | Amazon SQS or Kafka consumer groups/topic retention | Buffers events for worker and notifier processes |
| Caching | Amazon ElastiCache Redis or Vultr Managed Valkey | Caches inventory and alert reads for the API |
| Database | Amazon DynamoDB or Vultr Managed PostgreSQL | Stores inventory, reorder alerts, and notification audit records |

The project uses all four listed technology categories even though the assignment requires only three.

## Three Processes

| Executable | Deployment target | Responsibility |
| --- | --- | --- |
| `inventory-api` | EC2 VM | HTTP entry point and read API |
| `inventory-worker` | EC2 VM | Inventory event consumer and reorder evaluator |
| `alert-notifier` | EC2 VM | Alert event consumer and notification audit recorder |

## Scalability and Efficiency

The API can accept requests quickly because it publishes to SNS and returns `202 Accepted` instead of doing all work synchronously. SQS decouples the API from the worker so a burst of inventory updates does not immediately overload the evaluation process. The worker can be scaled by running additional VM processes against the same queue. DynamoDB uses on-demand billing so table capacity adjusts without manual capacity planning for this class-sized workload. Redis reduces repeated DynamoDB reads for common dashboard calls such as open alerts.

## Cloud Deployment Strategy

The chosen deployment strategy is three cloud VMs plus managed cloud services. On AWS, the VMs are EC2 instances and the managed services are SNS, SQS, DynamoDB, and ElastiCache. On Vultr, the VMs are Cloud Compute instances and the managed services are Kafka, PostgreSQL, and Valkey. This is more operationally explicit than a serverless design, but it matches the assignment restrictions. The application logic runs on VMs, while the cloud provider manages the stateful services. That means the project demonstrates cloud integration without hiding the three executables inside prohibited functions or containers.

## Testing and Demonstration

Local automated tests cover the reorder decision rule and message decoding behavior. The cloud demonstration should show:

- A low-stock `POST /inventory` request returning `202 Accepted`.
- The inventory worker consuming the queued event.
- A DynamoDB inventory record.
- A DynamoDB open alert record.
- The alert notifier recording a notification audit item.
- `GET /alerts` returning the open alert.
- A repeated `GET /alerts` returning a Redis cache hit.

## Rubric Alignment

| Rubric criterion | Evidence in this repository |
| --- | --- |
| End-to-end working project | Demo commands, service logs, DynamoDB records, screenshot checklist |
| Distributed application | Three separate executables coordinated by SNS/SQS |
| Cloud integration | Terraform creates AWS or Vultr VM and managed-service infrastructure |
| Technology components | Uses messaging, queuing, caching, and databases |
| Report completeness | This report plus deployment guide and architecture diagram |
| Source code quality | Python package, clear modules, tests, explicit environment config |
| Real-world relevance | Retail inventory reorder workflow |

## Limitations

The notification process records an audit event instead of sending email or SMS. That is deliberate: adding an email or SMS provider would introduce another application component outside the assignment's allowed set. The audit table still proves that the alert event moved through the distributed workflow.
