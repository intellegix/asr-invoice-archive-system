# ASR Records Legacy Frontend - Main Terraform Configuration
# Production-ready AWS ECS deployment with multi-tenant support
# Components: VPC, ECS, ALB, S3, RDS, CloudWatch

terraform {
  required_version = ">= 1.0"

  # Configure backend for state management
  # For development, use local backend. For production, configure S3 backend.
  # backend "s3" {
  #   bucket         = "asr-records-terraform-state-${var.environment}"
  #   key            = "legacy-frontend/terraform.tfstate"
  #   region         = "us-west-2"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

# Local variables for common configurations
locals {
  common_tags = {
    Project     = "ASR-Records-Legacy"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "ASR-Inc"
  }

  # Multi-tenant configuration
  tenant_config = var.tenant_configs

  # Networking
  vpc_cidr = var.vpc_cidr
  availability_zones = data.aws_availability_zones.available.names

  # ECS Configuration
  app_name = "asr-records-legacy"
  container_port = 8000
  frontend_port = 80

  # Security
  allowed_cidr_blocks = var.allowed_cidr_blocks
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

###########################################
# VPC and Networking
###########################################

resource "aws_vpc" "main" {
  cidr_block           = local.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-vpc-${var.environment}"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-igw-${var.environment}"
  })
}

# Public Subnets for ALB
resource "aws_subnet" "public" {
  count = min(length(local.availability_zones), 3)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(local.vpc_cidr, 4, count.index)
  availability_zone       = local.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-public-${count.index + 1}-${var.environment}"
    Type = "Public"
  })
}

# Private Subnets for ECS Tasks
resource "aws_subnet" "private" {
  count = min(length(local.availability_zones), 3)

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(local.vpc_cidr, 4, count.index + 3)
  availability_zone = local.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-private-${count.index + 1}-${var.environment}"
    Type = "Private"
  })
}

# Database Subnets for RDS
resource "aws_subnet" "database" {
  count = min(length(local.availability_zones), 3)

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(local.vpc_cidr, 4, count.index + 6)
  availability_zone = local.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-db-${count.index + 1}-${var.environment}"
    Type = "Database"
  })
}

# NAT Gateways for private subnet internet access
resource "aws_eip" "nat" {
  count = min(length(aws_subnet.public), var.enable_nat_gateway ? var.single_nat_gateway ? 1 : length(aws_subnet.public) : 0)

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-nat-eip-${count.index + 1}-${var.environment}"
  })
}

resource "aws_nat_gateway" "main" {
  count = min(length(aws_subnet.public), var.enable_nat_gateway ? var.single_nat_gateway ? 1 : length(aws_subnet.public) : 0)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-nat-gw-${count.index + 1}-${var.environment}"
  })

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-public-rt-${var.environment}"
  })
}

resource "aws_route_table" "private" {
  count = var.enable_nat_gateway ? var.single_nat_gateway ? 1 : length(aws_subnet.private) : 0

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[var.single_nat_gateway ? 0 : count.index].id
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-private-rt-${var.single_nat_gateway ? "shared" : count.index + 1}-${var.environment}"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = var.enable_nat_gateway ? aws_route_table.private[var.single_nat_gateway ? 0 : count.index].id : aws_route_table.public.id
}

###########################################
# Security Groups
###########################################

# ALB Security Group
resource "aws_security_group" "alb" {
  name_prefix = "${local.app_name}-alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = local.allowed_cidr_blocks
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = local.allowed_cidr_blocks
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-alb-sg-${var.environment}"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# ECS Security Group
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${local.app_name}-ecs-tasks-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Backend API"
    from_port       = local.container_port
    to_port         = local.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description     = "Frontend"
    from_port       = local.frontend_port
    to_port         = local.frontend_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-ecs-sg-${var.environment}"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "${local.app_name}-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_name}-rds-sg-${var.environment}"
  })

  lifecycle {
    create_before_destroy = true
  }
}

###########################################
# S3 Bucket for Multi-Tenant Documents
###########################################

resource "aws_s3_bucket" "documents" {
  bucket = var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.app_name}-documents-${var.environment}-${random_id.bucket_suffix.hex}"

  tags = merge(local.common_tags, {
    Name = "ASR Records Documents Storage"
    Purpose = "Multi-tenant document storage"
  })
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# TEMPORARILY COMMENTED OUT: IAM permissions issue
# TODO: Uncomment and configure proper IAM after resolving permissions
#
# S3 Bucket Policy for tenant isolation
# resource "aws_s3_bucket_policy" "documents" {
#   bucket = aws_s3_bucket.documents.id
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Sid    = "AllowECSTaskRole"
#         Effect = "Allow"
#         Principal = {
#           AWS = aws_iam_role.ecs_task_role.arn
#         }
#         Action = [
#           "s3:GetObject",
#           "s3:PutObject",
#           "s3:DeleteObject",
#           "s3:ListBucket"
#         ]
#         Resource = [
#           aws_s3_bucket.documents.arn,
#           "${aws_s3_bucket.documents.arn}/*"
#         ]
#       }
#     ]
#   })
# }

# Lifecycle configuration for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    id     = "tenant_cleanup"
    status = "Enabled"

    filter {
      prefix = "tenants/"
    }

    expiration {
      days = var.document_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

###########################################
# RDS Database
###########################################

resource "aws_db_subnet_group" "main" {
  name       = "${local.app_name}-db-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.database[*].id

  tags = merge(local.common_tags, {
    Name = "${local.app_name} DB Subnet Group"
  })
}

resource "aws_db_instance" "postgres" {
  identifier = "${local.app_name}-db-${var.environment}"

  engine         = "postgres"
  engine_version = var.postgres_version
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = var.db_backup_retention_period
  backup_window          = var.db_backup_window
  maintenance_window     = var.db_maintenance_window

  skip_final_snapshot = var.environment != "prod"
  deletion_protection = var.environment == "prod"

  # Performance Insights
  performance_insights_enabled = var.environment == "prod"
  performance_insights_retention_period = var.environment == "prod" ? 7 : 0

  # Monitoring
  monitoring_interval = var.environment == "prod" ? 60 : 0
  monitoring_role_arn = var.environment == "prod" ? aws_iam_role.rds_enhanced_monitoring[0].arn : null

  tags = merge(local.common_tags, {
    Name = "${local.app_name} PostgreSQL Database"
  })
}

# Enhanced monitoring role for RDS (production only)
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.environment == "prod" ? 1 : 0

  name_prefix = "${local.app_name}-rds-monitoring-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count = var.environment == "prod" ? 1 : 0

  role       = aws_iam_role.rds_enhanced_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

###########################################
# IAM Roles and Policies
###########################################

# TEMPORARILY COMMENTED OUT: IAM permissions issue
# TODO: Uncomment after resolving IAM permissions with AWS administrator
# User 'asr-po-migration' lacks iam:CreateRole permission
#
# ECS Task Execution Role
# resource "aws_iam_role" "ecs_task_execution_role" {
#   name_prefix = "${local.app_name}-ecs-execution-"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "ecs-tasks.amazonaws.com"
#         }
#       }
#     ]
#   })
#
#   tags = local.common_tags
# }
#
# resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
#   role       = aws_iam_role.ecs_task_execution_role.name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
# }
#
# ECS Task Role (for application permissions)
# resource "aws_iam_role" "ecs_task_role" {
#   name_prefix = "${local.app_name}-ecs-task-"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "ecs-tasks.amazonaws.com"
#         }
#       }
#     ]
#   })
#
#   tags = local.common_tags
# }

# TEMPORARILY COMMENTED OUT: IAM permissions issue
# TODO: Uncomment after resolving IAM permissions
#
# S3 access policy for ECS tasks
# resource "aws_iam_role_policy" "ecs_task_s3_policy" {
#   name_prefix = "${local.app_name}-s3-access-"
#   role        = aws_iam_role.ecs_task_role.id
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "s3:GetObject",
#           "s3:PutObject",
#           "s3:DeleteObject",
#           "s3:ListBucket"
#         ]
#         Resource = [
#           aws_s3_bucket.documents.arn,
#           "${aws_s3_bucket.documents.arn}/*"
#         ]
#       }
#     ]
#   })
# }
#
# Secrets Manager access for sensitive configuration
# resource "aws_iam_role_policy" "ecs_task_secrets_policy" {
#   name_prefix = "${local.app_name}-secrets-access-"
#   role        = aws_iam_role.ecs_task_role.id
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "secretsmanager:GetSecretValue"
#         ]
#         Resource = [
#           "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${local.app_name}/*"
#         ]
#       }
#     ]
#   })
# }

###########################################
# CloudWatch Log Groups
###########################################

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.app_name}-backend-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name = "${local.app_name} Backend Logs"
  })
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.app_name}-frontend-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name = "${local.app_name} Frontend Logs"
  })
}