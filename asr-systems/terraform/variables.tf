# ASR Records — Consolidated Terraform Variables
# All variable definitions in one place. Individual .tf files reference these.

# ---------- Global ----------

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# ---------- Networking (RDS) ----------

variable "vpc_id" {
  description = "VPC ID for security groups"
  type        = string
}

variable "private_subnet_ids" {
  description = "Subnet IDs for the RDS subnet group"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group attached to ECS tasks (allowed to reach RDS)"
  type        = string
}

# ---------- Database ----------

variable "db_password" {
  description = "Master password for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true
}

# ---------- CloudWatch ----------

variable "ecs_cluster_name" {
  description = "ECS cluster name for CloudWatch dimensions"
  type        = string
  default     = "asr-records-legacy-cluster-dev"
}

variable "backend_service_name" {
  description = "Backend ECS service name for CloudWatch dimensions"
  type        = string
  default     = "backend-service"
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications (leave empty to skip)"
  type        = string
  default     = ""
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix (e.g. app/asr-records-alb/1234567890)"
  type        = string
  default     = ""
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix for 5xx alarm"
  type        = string
  default     = ""
}

# ---------- SNS ----------

variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = ""
}
