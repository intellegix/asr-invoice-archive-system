# ASR Records Legacy Frontend - Terraform Outputs
# Infrastructure resource outputs for integration and monitoring

###########################################
# Networking Outputs
###########################################

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  description = "List of database subnet IDs"
  value       = aws_subnet.database[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

###########################################
# Security Group Outputs
###########################################

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS tasks security group"
  value       = aws_security_group.ecs_tasks.id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds.id
}

###########################################
# S3 Storage Outputs
###########################################

output "documents_bucket_name" {
  description = "Name of the S3 bucket for documents"
  value       = aws_s3_bucket.documents.bucket
}

output "documents_bucket_arn" {
  description = "ARN of the S3 bucket for documents"
  value       = aws_s3_bucket.documents.arn
}

output "documents_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.documents.bucket_domain_name
}

output "documents_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.documents.bucket_regional_domain_name
}

###########################################
# Database Outputs
###########################################

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "database_port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgres.port
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.postgres.db_name
}

output "database_username" {
  description = "Database master username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "database_identifier" {
  description = "RDS instance identifier"
  value       = aws_db_instance.postgres.identifier
}

output "database_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.postgres.arn
}

output "database_subnet_group" {
  description = "Database subnet group name"
  value       = aws_db_subnet_group.main.name
}

###########################################
# IAM Role Outputs
###########################################

# TEMPORARILY COMMENTED OUT: IAM permissions issue
# TODO: Uncomment after resolving IAM permissions
#
# output "ecs_task_execution_role_arn" {
#   description = "ARN of the ECS task execution role"
#   value       = aws_iam_role.ecs_task_execution_role.arn
# }
#
# output "ecs_task_role_arn" {
#   description = "ARN of the ECS task role"
#   value       = aws_iam_role.ecs_task_role.arn
# }
#
# output "ecs_task_execution_role_name" {
#   description = "Name of the ECS task execution role"
#   value       = aws_iam_role.ecs_task_execution_role.name
# }
#
# output "ecs_task_role_name" {
#   description = "Name of the ECS task role"
#   value       = aws_iam_role.ecs_task_role.name
# }

###########################################
# CloudWatch Outputs
###########################################

output "backend_log_group_name" {
  description = "Backend CloudWatch log group name"
  value       = aws_cloudwatch_log_group.backend.name
}

output "backend_log_group_arn" {
  description = "Backend CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.backend.arn
}

output "frontend_log_group_name" {
  description = "Frontend CloudWatch log group name"
  value       = aws_cloudwatch_log_group.frontend.name
}

output "frontend_log_group_arn" {
  description = "Frontend CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.frontend.arn
}

###########################################
# Application Configuration Outputs
###########################################

output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "tenant_configs" {
  description = "Configured tenants"
  value       = var.tenant_configs
  sensitive   = true
}

###########################################
# Infrastructure Metadata
###########################################

output "deployment_timestamp" {
  description = "Infrastructure deployment timestamp"
  value       = timestamp()
}

output "terraform_workspace" {
  description = "Terraform workspace used for deployment"
  value       = terraform.workspace
}

output "aws_account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = data.aws_availability_zones.available.names
}

###########################################
# Resource Tags
###########################################

output "common_tags" {
  description = "Common tags applied to resources"
  value = {
    Project     = "ASR-Records-Legacy"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "ASR-Inc"
  }
}

###########################################
# ECS Configuration for Task Definitions
###########################################

output "ecs_cluster_name" {
  description = "ECS cluster name for task definitions"
  value       = "${local.app_name}-cluster-${var.environment}"
}

output "ecs_service_names" {
  description = "ECS service names for deployment"
  value = {
    backend  = "${local.app_name}-backend-${var.environment}"
    frontend = "${local.app_name}-frontend-${var.environment}"
  }
}

###########################################
# Database Connection String
###########################################

output "database_connection_string" {
  description = "Database connection string for application configuration"
  value       = "postgresql://${aws_db_instance.postgres.username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
}

###########################################
# S3 Configuration for Application
###########################################

output "s3_configuration" {
  description = "S3 configuration for application"
  value = {
    bucket_name = aws_s3_bucket.documents.bucket
    region      = var.aws_region
    endpoint    = "https://s3.${var.aws_region}.amazonaws.com"
  }
}

###########################################
# Monitoring Endpoints
###########################################

output "monitoring_endpoints" {
  description = "Monitoring and management endpoints"
  value = {
    cloudwatch_logs = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups"
    rds_console     = "https://${var.aws_region}.console.aws.amazon.com/rds/home?region=${var.aws_region}#database:id=${aws_db_instance.postgres.identifier}"
    s3_console      = "https://s3.console.aws.amazon.com/s3/buckets/${aws_s3_bucket.documents.bucket}"
    ecs_console     = "https://${var.aws_region}.console.aws.amazon.com/ecs/home?region=${var.aws_region}#/clusters"
  }
}

###########################################
# Security Information
###########################################

output "security_configuration" {
  description = "Security configuration summary"
  value = {
    s3_encryption_enabled    = true
    rds_encryption_enabled   = true
    vpc_flow_logs_enabled    = false
    secrets_manager_enabled  = true
    iam_roles_created        = 2
  }
}

###########################################
# Cost Optimization Information
###########################################

output "cost_optimization" {
  description = "Cost optimization features enabled"
  value = {
    s3_lifecycle_enabled     = true
    rds_deletion_protection  = var.environment == "prod"
    nat_gateway_count        = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(aws_subnet.public)) : 0
    spot_instances_enabled   = var.enable_spot_instances
    log_retention_days       = var.log_retention_days
  }
}

###########################################
# Multi-Tenant Information
###########################################

output "multi_tenant_configuration" {
  description = "Multi-tenant setup information"
  value = {
    tenant_isolation_method = "S3 prefix-based isolation"
    s3_bucket_structure     = "tenants/{tenant_id}/{category}/{file}"
    database_isolation      = "Schema-based tenant isolation"
    supported_tenants       = length(var.tenant_configs)
  }
  sensitive = true
}