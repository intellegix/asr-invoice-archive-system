# ASR Records Legacy - Development Environment Configuration
# Terraform variables for development deployment

###########################################
# Environment Configuration
###########################################
environment = "dev"
aws_region  = "us-west-2"

###########################################
# Networking Configuration
###########################################
vpc_cidr = "10.0.0.0/16"
allowed_cidr_blocks = ["0.0.0.0/0"]  # Open access for development

# Cost optimization for dev environment
enable_nat_gateway  = false  # Use public subnets for dev to save costs
single_nat_gateway  = false

###########################################
# Multi-Tenant Configuration (Development)
###########################################
tenant_configs = {
  "dev-tenant-1" = {
    subdomain        = "dev1"
    gl_accounts      = ["1000", "1100", "2000", "5000"]
    payment_methods  = ["claude_vision", "claude_text"]
    storage_quota_gb = 5
    user_limit       = 5
    active           = true
  }
  "dev-tenant-2" = {
    subdomain        = "dev2"
    gl_accounts      = ["1000", "1200", "3000"]
    payment_methods  = ["regex", "amount_analysis"]
    storage_quota_gb = 3
    user_limit       = 3
    active           = true
  }
}

###########################################
# S3 Storage Configuration
###########################################
# s3_bucket_name left empty for auto-generation
document_retention_days = 30  # Shorter retention for dev

###########################################
# Database Configuration (Development)
###########################################
db_name                    = "asr_records_dev"
db_username                = "asr_dev_admin"
# db_password should be set via environment variable or prompted
postgres_version           = "15.15"
db_instance_class         = "db.t3.micro"  # Minimal instance for dev
db_allocated_storage      = 20
db_max_allocated_storage  = 50
db_backup_retention_period = 1  # Minimal backup for dev
db_backup_window          = "07:00-08:00"
db_maintenance_window     = "Sun:08:00-Sun:09:00"

###########################################
# ECS Configuration (Development)
###########################################
# Minimal resources for development
backend_cpu           = 256
backend_memory        = 512
backend_desired_count = 1
backend_max_capacity  = 2

frontend_cpu           = 256
frontend_memory        = 512
frontend_desired_count = 1
frontend_max_capacity  = 2

ecr_repository_prefix = "asr-records-legacy-dev"

###########################################
# Application Configuration
###########################################
# anthropic_api_key should be set via environment variable or prompted
api_rate_limit           = 100  # Lower rate limit for dev
enable_debug            = true
cors_allowed_origins    = ["*"]  # Open CORS for dev

###########################################
# Monitoring and Logging
###########################################
log_retention_days               = 3  # Short retention for dev
enable_performance_insights      = false
enable_container_insights        = true
cloudwatch_dashboard_enabled     = true

###########################################
# Security Configuration
###########################################
enable_waf           = false
ssl_certificate_arn  = ""  # No SSL for dev
force_ssl_redirect   = false

###########################################
# Auto-scaling Configuration
###########################################
enable_autoscaling      = false  # Disable auto-scaling for dev
autoscaling_target_cpu  = 80
autoscaling_target_memory = 90

###########################################
# Domain and DNS Configuration
###########################################
domain_name              = ""  # Use default ALB DNS for dev
route53_zone_id          = ""
enable_subdomain_routing = false

###########################################
# Backup and Disaster Recovery
###########################################
enable_point_in_time_recovery = false
backup_schedule              = ""  # No scheduled backups for dev
cross_region_backup          = false
backup_retention_period      = 7

###########################################
# Cost Optimization
###########################################
enable_spot_instances         = true   # Use spot for cost savings in dev
spot_allocation_strategy      = "diversified"
enable_s3_intelligent_tiering = false  # Not needed for small dev datasets

###########################################
# Compliance and Governance
###########################################
enable_config_rules      = false
enable_cloudtrail        = false
data_residency_region    = ""
encryption_kms_key_id    = ""  # Use AWS managed keys