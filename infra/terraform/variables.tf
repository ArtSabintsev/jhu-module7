variable "aws_region" {
  description = "AWS region for the module project."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for all named AWS resources."
  type        = string
  default     = "jhu-module7"
}

variable "ssh_cidr" {
  description = "CIDR block allowed to SSH to the EC2 instances."
  type        = string
}

variable "api_cidr" {
  description = "CIDR block allowed to call the API service."
  type        = string
  default     = "0.0.0.0/0"
}

variable "ec2_instance_type" {
  description = "EC2 instance type for the three executables."
  type        = string
  default     = "t3.micro"
}

variable "redis_node_type" {
  description = "ElastiCache node type for Redis."
  type        = string
  default     = "cache.t4g.micro"
}

variable "key_name" {
  description = "Existing EC2 key pair name for SSH access."
  type        = string
}

variable "app_repo_url" {
  description = "Optional git URL to clone on each EC2 instance. Use HTTPS for public repos or SSH with an appropriate deploy key."
  type        = string
  default     = ""
}

variable "app_git_ref" {
  description = "Git branch, tag, or commit to check out if app_repo_url is set."
  type        = string
  default     = "main"
}
