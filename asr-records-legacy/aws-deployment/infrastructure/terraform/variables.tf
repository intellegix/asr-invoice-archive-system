# ASR Records Legacy Frontend - Terraform Variables
# Configurable parameters for infrastructure deployment

###########################################
# Environment Configuration
###########################################

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

###########################################
# Networking Configuration
###########################################

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnet internet access"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT gateway for all private subnets (cost optimization)"
  type        = bool
  default     = true
}

###########################################
# Multi-Tenant Configuration
###########################################

variable "tenant_configs" {
  description = "Tenant-specific configurations"
  type = map(object({
    subdomain        = string
    gl_accounts      = list(string)
    payment_methods  = list(string)
    storage_quota_gb = number
    user_limit       = number
    active           = bool
  }))
  default = {
    "default" = {
      subdomain        = "app"
      gl_accounts      = ["1000", "1100", "2000", "5000"]
      payment_methods  = ["claude_vision", "claude_text", "regex"]
      storage_quota_gb = 10
      user_limit       = 10
      active           = true
    }
  }
}

###########################################
# S3 Storage Configuration
###########################################

variable "s3_bucket_name" {
  description = "S3 bucket name for document storage (leave empty for auto-generated)"
  type        = string
  default     = ""
}

variable "document_retention_days" {
  description = "Number of days to retain documents (for compliance/cost optimization)"
  type        = number
  default     = 2555  # 7 years for tax compliance
}

###########################################
# Database Configuration
###########################################

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "asr_records"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "asr_admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.4"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial database storage (GB)"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum database storage for auto-scaling (GB)"
  type        = number
  default     = 100
}

variable "db_backup_retention_period" {
  description = "Database backup retention period (days)"
  type        = number
  default     = 7
}

variable "db_backup_window" {
  description = "Database backup window (UTC)"
  type        = string
  default     = "07:00-09:00"
}

variable "db_maintenance_window" {
  description = "Database maintenance window (UTC)"
  type        = string
  default     = "Sun:09:00-Sun:11:00"
}

###########################################
# ECS Configuration
###########################################

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = ""  # Auto-generated from app name and environment
}

variable "backend_cpu" {
  description = "Backend service CPU units"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Backend service memory (MB)"
  type        = number
  default     = 1024
}

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 1
}

variable "backend_max_capacity" {
  description = "Maximum number of backend tasks for auto-scaling"
  type        = number
  default     = 4
}

variable "frontend_cpu" {
  description = "Frontend service CPU units"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Frontend service memory (MB)"
  type        = number
  default     = 512
}

variable "frontend_desired_count" {
  description = "Desired number of frontend tasks"
  type        = number
  default     = 1
}

variable "frontend_max_capacity" {
  description = "Maximum number of frontend tasks for auto-scaling"
  type        = number
  default     = 3
}

###########################################
# Container Image Configuration
###########################################

variable "backend_image" {
  description = "Backend Docker image URI"
  type        = string
  default     = ""  # Will be set during deployment
}

variable "frontend_image" {
  description = "Frontend Docker image URI"
  type        = string
  default     = ""  # Will be set during deployment
}

variable "ecr_repository_prefix" {
  description = "ECR repository prefix for images"
  type        = string
  default     = "asr-records-legacy"
}

###########################################
# Application Configuration
###########################################

variable "anthropic_api_key" {
  description = "Anthropic Claude API key for document processing"
  type        = string
  sensitive   = true
  default     = ""
}

variable "api_rate_limit" {
  description = "API rate limit (requests per minute)"
  type        = number
  default     = 1000
}

variable "enable_debug" {
  description = "Enable debug mode for applications"
  type        = bool
  default     = false
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins for API"
  type        = list(string)
  default     = ["*"]
}

###########################################
# Monitoring and Logging
###########################################

variable "log_retention_days" {
  description = "CloudWatch log retention period (days)"
  type        = number
  default     = 14
}

variable "enable_performance_insights" {
  description = "Enable RDS Performance Insights"
  type        = bool
  default     = false
}

variable "enable_container_insights" {
  description = "Enable ECS Container Insights"
  type        = bool
  default     = true
}

variable "cloudwatch_dashboard_enabled" {
  description = "Enable CloudWatch dashboard creation"
  type        = bool
  default     = true
}

###########################################
# Security Configuration
###########################################

variable "enable_waf" {
  description = "Enable AWS WAF for additional security"
  type        = bool
  default     = false
}

variable "ssl_certificate_arn" {
  description = "SSL certificate ARN for HTTPS (leave empty to skip HTTPS)"
  type        = string
  default     = ""
}

variable "force_ssl_redirect" {
  description = "Force HTTP to HTTPS redirect"
  type        = bool
  default     = false
}

###########################################
# Auto-scaling Configuration
###########################################

variable "enable_autoscaling" {
  description = "Enable ECS service auto-scaling"
  type        = bool
  default     = true
}

variable "autoscaling_target_cpu" {
  description = "Target CPU utilization for auto-scaling"
  type        = number
  default     = 70
}

variable "autoscaling_target_memory" {
  description = "Target memory utilization for auto-scaling"
  type        = number
  default     = 80
}

variable "scale_up_cooldown" {
  description = "Scale up cooldown period (seconds)"
  type        = number
  default     = 300
}

variable "scale_down_cooldown" {
  description = "Scale down cooldown period (seconds)"
  type        = number
  default     = 300
}

###########################################
# Domain and DNS Configuration
###########################################

variable "domain_name" {
  description = "Domain name for the application (e.g., asr-records.com)"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for domain"
  type        = string
  default     = ""
}

variable "enable_subdomain_routing" {
  description = "Enable tenant-specific subdomain routing"
  type        = bool
  default     = true
}

###########################################
# Backup and Disaster Recovery
###########################################

variable "enable_point_in_time_recovery" {
  description = "Enable RDS point-in-time recovery"
  type        = bool
  default     = true
}

variable "backup_schedule" {
  description = "CloudWatch Events schedule for automated backups"
  type        = string
  default     = "rate(24 hours)"
}

variable "cross_region_backup" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Backup retention period (days)"
  type        = number
  default     = 30
}

###########################################
# Cost Optimization
###########################################

variable "enable_spot_instances" {
  description = "Enable Spot instances for ECS tasks (cost optimization)"
  type        = bool
  default     = false
}

variable "spot_allocation_strategy" {
  description = "Spot instance allocation strategy"
  type        = string
  default     = "diversified"
}

variable "enable_s3_intelligent_tiering" {
  description = "Enable S3 Intelligent Tiering for cost optimization"
  type        = bool
  default     = true
}

###########################################
# Compliance and Governance
###########################################

variable "enable_config_rules" {
  description = "Enable AWS Config compliance rules"
  type        = bool
  default     = false
}

variable "enable_cloudtrail" {
  description = "Enable CloudTrail for audit logging"
  type        = bool
  default     = false
}

variable "data_residency_region" {
  description = "Required data residency region for compliance"
  type        = string
  default     = ""
}

variable "encryption_kms_key_id" {
  description = "KMS key ID for encryption (leave empty for AWS managed keys)"
  type        = string
  default     = ""
}