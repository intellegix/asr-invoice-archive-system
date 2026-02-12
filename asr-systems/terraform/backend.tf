# ASR Records — Terraform Remote State Backend
# S3 bucket + DynamoDB table for state locking.
#
# Bootstrap (one-time):
#   1. Create the S3 bucket:
#        aws s3api create-bucket --bucket asr-records-terraform-state \
#          --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2
#   2. Enable versioning:
#        aws s3api put-bucket-versioning --bucket asr-records-terraform-state \
#          --versioning-configuration Status=Enabled
#   3. Create the DynamoDB lock table:
#        aws dynamodb create-table --table-name asr-records-terraform-locks \
#          --attribute-definitions AttributeName=LockID,AttributeType=S \
#          --key-schema AttributeName=LockID,KeyType=HASH \
#          --billing-mode PAY_PER_REQUEST --region us-west-2
#   4. Run: terraform init

terraform {
  backend "s3" {
    bucket         = "asr-records-terraform-state"
    key            = "asr-records/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "asr-records-terraform-locks"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.5.0"
}

provider "aws" {
  region = "us-west-2"

  default_tags {
    tags = {
      Project     = "asr-records"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}
