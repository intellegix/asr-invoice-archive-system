# ASR Records — PostgreSQL RDS Instance (dev)
#
# db.t3.micro is free-tier eligible and sufficient for development.
# Production should upgrade to db.t3.small or larger.

resource "aws_db_subnet_group" "asr" {
  name       = "asr-records-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name    = "asr-records-db-subnet-group"
    Project = "asr-records"
    Env     = var.environment
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "asr-records-rds-"
  vpc_id      = var.vpc_id
  description = "Allow inbound PostgreSQL from ECS tasks"

  ingress {
    description     = "PostgreSQL from ECS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "asr-records-rds-sg"
    Project = "asr-records"
  }
}

resource "aws_db_instance" "asr" {
  identifier     = "asr-records-${var.environment}"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "asr_records"
  username = "asr_admin"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.asr.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az            = false
  publicly_accessible = false
  skip_final_snapshot = var.environment == "dev" ? true : false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  deletion_protection = var.environment == "prod" ? true : false

  tags = {
    Name    = "asr-records-db-${var.environment}"
    Project = "asr-records"
    Env     = var.environment
  }
}

# Store the connection string in Secrets Manager (matches backend-task-def.json)
resource "aws_secretsmanager_secret" "db_url" {
  name        = "asr-records/database-url"
  description = "PostgreSQL connection URL for ASR Records backend"
}

resource "aws_secretsmanager_secret_version" "db_url" {
  secret_id     = aws_secretsmanager_secret.db_url.id
  secret_string = "postgresql://${aws_db_instance.asr.username}:${var.db_password}@${aws_db_instance.asr.endpoint}/${aws_db_instance.asr.db_name}"
}

# ---------- Variables expected by this file ----------

variable "private_subnet_ids" {
  description = "Subnet IDs for the RDS subnet group"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "ecs_security_group_id" {
  description = "Security group attached to ECS tasks (allowed to reach RDS)"
  type        = string
}

variable "db_password" {
  description = "Master password for the RDS instance"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# ---------- Outputs ----------

output "rds_endpoint" {
  value = aws_db_instance.asr.endpoint
}

output "rds_db_name" {
  value = aws_db_instance.asr.db_name
}
