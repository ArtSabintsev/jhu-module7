terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

locals {
  subnet_cidrs = {
    a = "10.70.1.0/24"
    b = "10.70.2.0/24"
  }

  subnet_az_index = {
    a = 0
    b = 1
  }

  common_tags = {
    Project = var.project_name
    Course  = "JHU Module 7"
  }

  services = {
    api = {
      executable = "inventory-api"
      port       = 8000
    }
    worker = {
      executable = "inventory-worker"
      port       = 0
    }
    notifier = {
      executable = "alert-notifier"
      port       = 0
    }
  }
}

resource "aws_vpc" "main" {
  cidr_block           = "10.70.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-vpc" })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, { Name = "${var.project_name}-igw" })
}

resource "aws_subnet" "public" {
  for_each = local.subnet_cidrs

  vpc_id                  = aws_vpc.main.id
  cidr_block              = each.value
  availability_zone       = data.aws_availability_zones.available.names[local.subnet_az_index[each.key]]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-public-${each.key}" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-public-rt" })
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "ec2" {
  name        = "${var.project_name}-ec2"
  description = "EC2 access for Module 7 application processes"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  ingress {
    description = "Inventory API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.api_cidr]
  }

  egress {
    description = "Outbound AWS API and package access"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-ec2-sg" })
}

resource "aws_security_group" "redis" {
  name        = "${var.project_name}-redis"
  description = "Allow Redis from the application EC2 instances"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from app servers"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-redis-sg" })
}

resource "aws_dynamodb_table" "inventory" {
  name         = "${var.project_name}-inventory"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "sku"

  attribute {
    name = "sku"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "alerts" {
  name         = "${var.project_name}-reorder-alerts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "alert_id"

  attribute {
    name = "alert_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "notifications" {
  name         = "${var.project_name}-notification-audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "notification_id"

  attribute {
    name = "notification_id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_sns_topic" "inventory_updates" {
  name = "${var.project_name}-inventory-updates"
  tags = local.common_tags
}

resource "aws_sns_topic" "reorder_alerts" {
  name = "${var.project_name}-reorder-alerts"
  tags = local.common_tags
}

resource "aws_sqs_queue" "inventory_worker" {
  name                       = "${var.project_name}-inventory-worker"
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 60
  tags                       = local.common_tags
}

resource "aws_sqs_queue" "alert_notifier" {
  name                       = "${var.project_name}-alert-notifier"
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 60
  tags                       = local.common_tags
}

data "aws_iam_policy_document" "inventory_queue" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }

    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.inventory_worker.arn]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.inventory_updates.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "inventory_worker" {
  queue_url = aws_sqs_queue.inventory_worker.id
  policy    = data.aws_iam_policy_document.inventory_queue.json
}

data "aws_iam_policy_document" "alert_queue" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }

    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.alert_notifier.arn]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.reorder_alerts.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "alert_notifier" {
  queue_url = aws_sqs_queue.alert_notifier.id
  policy    = data.aws_iam_policy_document.alert_queue.json
}

resource "aws_sns_topic_subscription" "inventory_to_queue" {
  topic_arn = aws_sns_topic.inventory_updates.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.inventory_worker.arn

  depends_on = [aws_sqs_queue_policy.inventory_worker]
}

resource "aws_sns_topic_subscription" "alert_to_queue" {
  topic_arn = aws_sns_topic.reorder_alerts.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.alert_notifier.arn

  depends_on = [aws_sqs_queue_policy.alert_notifier]
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-cache-subnets"
  subnet_ids = [for subnet in aws_subnet.public : subnet.id]
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = local.common_tags
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app" {
  name               = "${var.project_name}-app-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "app" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:Scan",
      "dynamodb:UpdateItem"
    ]
    resources = [
      aws_dynamodb_table.inventory.arn,
      aws_dynamodb_table.alerts.arn,
      aws_dynamodb_table.notifications.arn
    ]
  }

  statement {
    actions = ["sns:Publish"]
    resources = [
      aws_sns_topic.inventory_updates.arn,
      aws_sns_topic.reorder_alerts.arn
    ]
  }

  statement {
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes"
    ]
    resources = [
      aws_sqs_queue.inventory_worker.arn,
      aws_sqs_queue.alert_notifier.arn
    ]
  }
}

resource "aws_iam_policy" "app" {
  name   = "${var.project_name}-app-policy"
  policy = data.aws_iam_policy_document.app.json
}

resource "aws_iam_role_policy_attachment" "app" {
  role       = aws_iam_role.app.name
  policy_arn = aws_iam_policy.app.arn
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.project_name}-app-profile"
  role = aws_iam_role.app.name
}

resource "aws_instance" "service" {
  for_each = local.services

  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.ec2_instance_type
  key_name                    = var.key_name
  subnet_id                   = aws_subnet.public["a"].id
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.ec2.id]
  iam_instance_profile        = aws_iam_instance_profile.app.name

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    app_git_ref          = var.app_git_ref
    app_repo_url         = var.app_repo_url
    aws_region           = var.aws_region
    executable           = each.value.executable
    inventory_topic_arn  = aws_sns_topic.inventory_updates.arn
    alert_topic_arn      = aws_sns_topic.reorder_alerts.arn
    inventory_queue_url  = aws_sqs_queue.inventory_worker.id
    alert_queue_url      = aws_sqs_queue.alert_notifier.id
    inventory_table      = aws_dynamodb_table.inventory.name
    alert_table          = aws_dynamodb_table.alerts.name
    notification_table   = aws_dynamodb_table.notifications.name
    redis_endpoint       = aws_elasticache_cluster.redis.cache_nodes[0].address
  })

  tags = merge(local.common_tags, { Name = "${var.project_name}-${each.key}" })
}
