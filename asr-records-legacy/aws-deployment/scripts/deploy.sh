#!/bin/bash

# ASR Records Legacy - AWS Deployment Script
# Automated deployment script for Terraform infrastructure

set -euo pipefail  # Exit on error, undefined variables, pipe failures

###########################################
# Configuration
###########################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_DIR}/infrastructure/terraform"

# Default values
ENVIRONMENT="dev"
AWS_REGION="us-west-2"
AUTO_APPROVE="false"
PLAN_ONLY="false"
DESTROY="false"
INIT_UPGRADE="false"

###########################################
# Helper Functions
###########################################

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

error() {
    log "ERROR: $*"
    exit 1
}

usage() {
    cat << EOF
ASR Records Legacy - AWS Deployment Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -e, --environment ENVIRONMENT   Target environment (dev, staging, prod)
    -r, --region REGION            AWS region (default: us-west-2)
    -a, --auto-approve             Auto-approve Terraform changes
    -p, --plan-only                Only run terraform plan
    -d, --destroy                  Destroy infrastructure
    -u, --upgrade                  Upgrade Terraform providers
    -h, --help                     Show this help message

EXAMPLES:
    # Deploy to development environment
    $0 -e dev

    # Plan production deployment
    $0 -e prod -p

    # Deploy to production with auto-approve
    $0 -e prod -a

    # Destroy development environment
    $0 -e dev -d

    # Upgrade providers and deploy
    $0 -e dev -u
EOF
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        error "Terraform is not installed. Please install Terraform first."
    fi

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install AWS CLI first."
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured or invalid. Please run 'aws configure' first."
    fi

    # Check if required files exist
    if [[ ! -f "${TERRAFORM_DIR}/main.tf" ]]; then
        error "Terraform configuration not found at ${TERRAFORM_DIR}/main.tf"
    fi

    if [[ ! -f "${TERRAFORM_DIR}/environments/${ENVIRONMENT}.tfvars" ]]; then
        error "Environment configuration not found at ${TERRAFORM_DIR}/environments/${ENVIRONMENT}.tfvars"
    fi

    log "✓ Prerequisites check passed"
}

setup_terraform_backend() {
    log "Setting up Terraform backend..."

    # For production, you should use a remote backend
    # This script assumes local backend for simplicity
    local backend_config=""

    if [[ "${ENVIRONMENT}" == "prod" ]]; then
        log "WARNING: Using local backend for production. Consider configuring remote backend."
    fi

    log "✓ Terraform backend configured"
}

terraform_init() {
    log "Initializing Terraform..."

    cd "${TERRAFORM_DIR}"

    local init_args=""
    if [[ "${INIT_UPGRADE}" == "true" ]]; then
        init_args="-upgrade"
    fi

    terraform init ${init_args}

    log "✓ Terraform initialized"
}

terraform_plan() {
    log "Planning Terraform changes for ${ENVIRONMENT} environment..."

    cd "${TERRAFORM_DIR}"

    terraform plan \
        -var-file="environments/${ENVIRONMENT}.tfvars" \
        -var="aws_region=${AWS_REGION}" \
        -out="terraform-${ENVIRONMENT}.plan"

    log "✓ Terraform plan created"
}

terraform_apply() {
    log "Applying Terraform changes for ${ENVIRONMENT} environment..."

    cd "${TERRAFORM_DIR}"

    local apply_args=""
    if [[ "${AUTO_APPROVE}" == "true" ]]; then
        apply_args="-auto-approve"
    fi

    terraform apply ${apply_args} "terraform-${ENVIRONMENT}.plan"

    log "✓ Terraform changes applied successfully"
}

terraform_destroy() {
    log "Destroying infrastructure for ${ENVIRONMENT} environment..."

    cd "${TERRAFORM_DIR}"

    local destroy_args=""
    if [[ "${AUTO_APPROVE}" == "true" ]]; then
        destroy_args="-auto-approve"
    fi

    terraform destroy \
        ${destroy_args} \
        -var-file="environments/${ENVIRONMENT}.tfvars" \
        -var="aws_region=${AWS_REGION}"

    log "✓ Infrastructure destroyed"
}

show_outputs() {
    log "Retrieving Terraform outputs..."

    cd "${TERRAFORM_DIR}"

    echo
    echo "=== DEPLOYMENT OUTPUTS ==="
    terraform output -json | jq -r '
        to_entries[] |
        "\(.key): \(.value.value)"
    ' || terraform output

    echo
    log "✓ Deployment completed successfully"
}

###########################################
# Main Script
###########################################

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -r|--region)
                AWS_REGION="$2"
                shift 2
                ;;
            -a|--auto-approve)
                AUTO_APPROVE="true"
                shift
                ;;
            -p|--plan-only)
                PLAN_ONLY="true"
                shift
                ;;
            -d|--destroy)
                DESTROY="true"
                shift
                ;;
            -u|--upgrade)
                INIT_UPGRADE="true"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done

    # Validate environment
    if [[ ! "${ENVIRONMENT}" =~ ^(dev|staging|prod)$ ]]; then
        error "Invalid environment: ${ENVIRONMENT}. Must be one of: dev, staging, prod"
    fi

    log "Starting deployment for environment: ${ENVIRONMENT}"
    log "AWS Region: ${AWS_REGION}"
    log "Auto-approve: ${AUTO_APPROVE}"
    log "Plan only: ${PLAN_ONLY}"
    log "Destroy: ${DESTROY}"

    # Check prerequisites
    check_prerequisites

    # Setup backend
    setup_terraform_backend

    # Initialize Terraform
    terraform_init

    if [[ "${DESTROY}" == "true" ]]; then
        # Destroy infrastructure
        terraform_destroy
    else
        # Plan changes
        terraform_plan

        if [[ "${PLAN_ONLY}" == "false" ]]; then
            # Apply changes
            terraform_apply

            # Show outputs
            show_outputs
        else
            log "✓ Plan completed. Use without -p flag to apply changes."
        fi
    fi
}

# Run main function
main "$@"