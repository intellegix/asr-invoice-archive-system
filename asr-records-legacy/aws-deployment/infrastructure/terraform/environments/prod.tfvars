# ASR Records Legacy - Production Environment Configuration
# Terraform variables for production deployment

###########################################
# Environment Configuration
###########################################
environment = "prod"
aws_region  = "us-west-2"

###########################################
# Networking Configuration
###########################################
vpc_cidr = "10.0.0.0/16"
allowed_cidr_blocks = ["0.0.0.0/0"]  # Configure specific IP ranges in production

# Production networking for security and availability
enable_nat_gateway = true
single_nat_gateway = false  # Multiple NAT gateways for HA

###########################################
# Multi-Tenant Configuration (Production)
###########################################
tenant_configs = {
  "acme-corp" = {
    subdomain        = "acme"
    gl_accounts      = ["1000", "1100", "2000", "5000", "6000", "7000"]
    payment_methods  = ["claude_vision", "claude_text", "regex", "amount_analysis"]
    storage_quota_gb = 100
    user_limit       = 50
    active           = true
  }
  "tech-startup" = {
    subdomain        = "tech"
    gl_accounts      = ["1000", "1200", "3000", "6000"]
    payment_methods  = ["claude_vision", "amount_analysis"]
    storage_quota_gb = 50
    user_limit       = 25
    active           = true
  }
  "consulting-firm" = {
    subdomain        = "consulting"
    gl_accounts      = ["1000", "1100", "2000", "4000", "5000"]
    payment_methods  = ["claude_vision", "claude_text", "regex"]
    storage_quota_gb = 75
    user_limit       = 35
    active           = true
  }
}

###########################################
# S3 Storage Configuration
###########################################
# s3_bucket_name left empty for auto-generation with security suffix
document_retention_days = 2555  # 7 years for tax compliance

###########################################
# Database Configuration (Production)
###########################################
db_name                    = "asr_records_prod"
db_username                = "asr_admin"
# db_password should be set via AWS Secrets Manager in production
postgres_version           = "15.4"
db_instance_class         = "db.t3.medium"  # Production-ready instance
db_allocated_storage      = 100
db_max_allocated_storage  = 500
db_backup_retention_period = 7   # Full backup retention
db_backup_window          = "07:00-09:00"  # Low-traffic window
db_maintenance_window     = "Sun:09:00-Sun:11:00"

###########################################
# ECS Configuration (Production)
###########################################
# Production-ready resources with high availability
backend_cpu           = 1024
backend_memory        = 2048
backend_desired_count = 2     # Multiple instances for HA
backend_max_capacity  = 8     # Auto-scaling for load spikes

frontend_cpu           = 512
frontend_memory        = 1024
frontend_desired_count = 2     # Multiple instances for HA
frontend_max_capacity  = 6     # Auto-scaling for load spikes

ecr_repository_prefix = "asr-records-legacy"

###########################################
# Application Configuration
###########################################
# anthropic_api_key should be set via AWS Secrets Manager in production
api_rate_limit           = 5000  # Higher rate limit for production
enable_debug            = false
cors_allowed_origins    = ["https://asr-records.com", "https://*.asr-records.com"]

###########################################
# Monitoring and Logging
###########################################
log_retention_days               = 30  # Extended retention for production
enable_performance_insights      = true
enable_container_insights        = true
cloudwatch_dashboard_enabled     = true

###########################################
# Security Configuration
###########################################
enable_waf           = true
# ssl_certificate_arn should be set to actual certificate ARN
# ssl_certificate_arn = "arn:aws:acm:us-west-2:ACCOUNT:certificate/CERT-ID"
force_ssl_redirect   = true

###########################################
# Auto-scaling Configuration
###########################################
enable_autoscaling      = true
autoscaling_target_cpu  = 70   # Conservative CPU target
autoscaling_target_memory = 80  # Conservative memory target
scale_up_cooldown      = 300
scale_down_cooldown    = 600    # Longer cooldown for scale-down

###########################################
# Domain and DNS Configuration
###########################################
# domain_name              = "asr-records.com"
# route53_zone_id          = "Z1234567890ABC"
enable_subdomain_routing = true

###########################################
# Backup and Disaster Recovery
###########################################
enable_point_in_time_recovery = true
backup_schedule              = "rate(24 hours)"
cross_region_backup          = true
backup_retention_period      = 90  # Extended backup retention

###########################################
# Cost Optimization
###########################################
enable_spot_instances         = false  # Use on-demand for production reliability
spot_allocation_strategy      = "diversified"
enable_s3_intelligent_tiering = true   # Cost optimization for large datasets

###########################################
# Compliance and Governance
###########################################
enable_config_rules      = true
enable_cloudtrail        = true
data_residency_region    = "us-west-2"
# encryption_kms_key_id    = "arn:aws:kms:us-west-2:ACCOUNT:key/KEY-ID"