# ASR Records Legacy - AWS Deployment

Production-ready AWS deployment infrastructure for the ASR Records Legacy Frontend with multi-tenant support.

## 🏗️ Architecture Overview

- **ECS Fargate**: Container orchestration for frontend and backend services
- **Application Load Balancer**: High-availability load balancing with SSL termination
- **RDS PostgreSQL**: Managed database with multi-AZ deployment
- **S3**: Multi-tenant document storage with encryption
- **CloudWatch**: Comprehensive monitoring and logging
- **VPC**: Secure networking with public/private subnets

## 📁 Directory Structure

```
aws-deployment/
├── infrastructure/
│   └── terraform/
│       ├── main.tf              # Main infrastructure configuration
│       ├── variables.tf         # Variable definitions
│       ├── outputs.tf           # Infrastructure outputs
│       ├── versions.tf          # Provider versions
│       ├── environments/        # Environment-specific configurations
│       │   ├── dev.tfvars      # Development configuration
│       │   ├── staging.tfvars  # Staging configuration
│       │   └── prod.tfvars     # Production configuration
│       └── modules/            # Reusable Terraform modules
│           └── ecs/            # ECS cluster module
├── containers/                 # Container configurations
├── scripts/                    # Deployment and utility scripts
│   └── deploy.sh              # Main deployment script
└── docs/                      # Deployment documentation
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate permissions
   ```bash
   aws configure
   ```

2. **Terraform** installed (>= 1.5.0)
   ```bash
   # macOS
   brew install terraform

   # Windows
   choco install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
   ```

3. **Docker** installed for building container images

### Required AWS Permissions

Your AWS user/role needs the following permissions:
- EC2 (VPC, Subnets, Security Groups)
- ECS (Clusters, Services, Task Definitions)
- RDS (Database instances, Subnet groups)
- S3 (Bucket management, Policies)
- IAM (Roles, Policies for ECS)
- CloudWatch (Log groups, Metrics)
- Application Load Balancer

### Environment Setup

1. **Clone and navigate to the deployment directory**
   ```bash
   cd asr-records-legacy/aws-deployment
   ```

2. **Configure environment variables**
   ```bash
   # Set required variables
   export TF_VAR_db_password="your-secure-database-password"
   export TF_VAR_anthropic_api_key="your-claude-api-key"

   # Optional: Configure AWS region
   export AWS_DEFAULT_REGION="us-west-2"
   ```

3. **Review and customize environment configuration**
   ```bash
   # Edit the appropriate environment file
   vi infrastructure/terraform/environments/dev.tfvars
   ```

### Deployment Commands

#### Development Environment

```bash
# Plan deployment (recommended first step)
./scripts/deploy.sh -e dev -p

# Deploy infrastructure
./scripts/deploy.sh -e dev

# Deploy with auto-approval (use with caution)
./scripts/deploy.sh -e dev -a
```

#### Production Environment

```bash
# Plan production deployment
./scripts/deploy.sh -e prod -p

# Deploy to production (requires manual approval)
./scripts/deploy.sh -e prod

# Emergency destroy (use extreme caution)
./scripts/deploy.sh -e prod -d -a
```

#### Other Useful Commands

```bash
# Upgrade Terraform providers
./scripts/deploy.sh -e dev -u

# Destroy development environment
./scripts/deploy.sh -e dev -d

# Deploy to custom region
./scripts/deploy.sh -e dev -r us-east-1
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TF_VAR_db_password` | Database master password | Yes | - |
| `TF_VAR_anthropic_api_key` | Claude API key | Yes | - |
| `AWS_DEFAULT_REGION` | AWS deployment region | No | us-west-2 |

### Environment Files

Customize deployment by editing the appropriate `.tfvars` file:

- **`dev.tfvars`**: Development environment (minimal resources)
- **`staging.tfvars`**: Staging environment (production-like)
- **`prod.tfvars`**: Production environment (high availability)

Key configuration sections:

```hcl
# Multi-tenant configuration
tenant_configs = {
  "acme-corp" = {
    subdomain        = "acme"
    gl_accounts      = ["1000", "1100", "2000"]
    storage_quota_gb = 100
    user_limit       = 50
    active           = true
  }
}

# Resource sizing
backend_cpu    = 1024
backend_memory = 2048
backend_desired_count = 2

# Security settings
allowed_cidr_blocks = ["10.0.0.0/8"]
enable_waf         = true
force_ssl_redirect = true
```

## 🏭 Multi-Tenant Architecture

### Tenant Isolation

- **S3 Storage**: `s3://bucket/tenants/{tenant_id}/category/file`
- **Database**: Schema-based isolation with tenant_id columns
- **API Access**: X-Tenant-ID header-based routing
- **Subdomain Routing**: `{tenant}.asr-records.com`

### Adding New Tenants

1. Update the `tenant_configs` in your environment file:
   ```hcl
   tenant_configs = {
     "new-client" = {
       subdomain        = "newclient"
       gl_accounts      = ["1000", "1100"]
       payment_methods  = ["claude_vision"]
       storage_quota_gb = 50
       user_limit       = 25
       active           = true
     }
   }
   ```

2. Deploy the configuration:
   ```bash
   ./scripts/deploy.sh -e prod
   ```

## 📊 Monitoring and Maintenance

### CloudWatch Dashboards

After deployment, access monitoring through:
- **ECS Console**: Monitor service health and scaling
- **CloudWatch Logs**: Application logs and errors
- **RDS Console**: Database performance metrics
- **S3 Console**: Storage usage and access patterns

### Cost Optimization

The infrastructure includes several cost optimization features:

- **Auto-scaling**: Scales down during low usage
- **S3 Intelligent Tiering**: Automatic storage class optimization
- **Spot Instances**: Optional for development environments
- **Log Retention**: Configurable retention periods

### Backup and Disaster Recovery

- **RDS Automated Backups**: 7-day retention (configurable)
- **S3 Versioning**: Document version history
- **Cross-Region Replication**: Optional for production
- **Infrastructure as Code**: Complete environment recreation

## 🔐 Security Features

- **VPC Isolation**: Private subnets for application tier
- **Security Groups**: Principle of least privilege
- **S3 Encryption**: Server-side encryption (AES-256)
- **RDS Encryption**: Database encryption at rest
- **IAM Roles**: Service-specific permissions
- **WAF Protection**: Optional web application firewall

## 🆘 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity

   # Verify IAM permissions
   aws iam get-user
   ```

2. **Terraform State Lock**
   ```bash
   # Force unlock (use cautiously)
   cd infrastructure/terraform
   terraform force-unlock <LOCK_ID>
   ```

3. **Resource Limits**
   ```bash
   # Check service limits
   aws service-quotas list-service-quotas --service-code ecs
   ```

4. **Container Issues**
   ```bash
   # Check ECS service events
   aws ecs describe-services --cluster <cluster-name> --services <service-name>

   # Check CloudWatch logs
   aws logs describe-log-groups --log-group-name-prefix /ecs/
   ```

### Support Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **Terraform Documentation**: https://registry.terraform.io/providers/hashicorp/aws/
- **ASR Records Issues**: GitHub issues in the project repository

## 📈 Scaling and Performance

### Auto-scaling Configuration

The infrastructure automatically scales based on:
- **CPU Utilization**: Target 70% (configurable)
- **Memory Utilization**: Target 80% (configurable)
- **Custom Metrics**: Application-specific scaling triggers

### Performance Optimization

- **Multi-AZ RDS**: High availability database
- **ECS Service Mesh**: Optional service discovery
- **CloudFront CDN**: Optional content delivery network
- **Read Replicas**: Optional database read scaling

## 🔄 CI/CD Integration

The deployment can be integrated with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Deploy Infrastructure
  run: |
    cd asr-records-legacy/aws-deployment
    ./scripts/deploy.sh -e ${{ github.ref_name }} -a
```

## 📝 Version History

- **v1.0**: Initial production-ready infrastructure
- **v1.1**: Added multi-tenant support
- **v1.2**: Enhanced monitoring and auto-scaling
- **v1.3**: Security improvements and WAF integration

---

For additional support or questions, please refer to the project documentation or create an issue in the repository.