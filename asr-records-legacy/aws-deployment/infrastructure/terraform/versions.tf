# ASR Records Legacy Frontend - Terraform Versions
# Provider version constraints and requirements

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }

    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }

    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }

    template = {
      source  = "hashicorp/template"
      version = "~> 2.2"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  # Default tags applied to all resources
  default_tags {
    tags = {
      Project       = "ASR-Records-Legacy"
      Environment   = var.environment
      ManagedBy     = "Terraform"
      Owner         = "ASR-Inc"
      Repository    = "asr-records-legacy"
      Component     = "Infrastructure"
      CostCenter    = "Engineering"
      Compliance    = "SOC2"
      BackupPolicy  = "Standard"
    }
  }

  # Skip metadata API check for faster provider initialization
  skip_metadata_api_check     = true
  skip_region_validation      = false
  skip_credentials_validation = false

  # Retry configuration for API calls
  retry_mode      = "adaptive"
  max_retries     = 3

  # Assume role configuration (if using cross-account deployment)
  # assume_role {
  #   role_arn    = var.assume_role_arn
  #   session_name = "terraform-asr-records-${var.environment}"
  # }
}

# Configure Random Provider for generating unique resource names
provider "random" {}

# Configure Time Provider for timestamp operations
provider "time" {}

# Configure Local Provider for local file operations
provider "local" {}

# Configure Template Provider for configuration file generation
provider "template" {}

# Configure TLS Provider for certificate operations
provider "tls" {}