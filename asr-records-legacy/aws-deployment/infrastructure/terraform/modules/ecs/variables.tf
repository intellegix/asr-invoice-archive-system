# ASR Records Legacy - ECS Module Variables

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the ECS cluster will be deployed"
  type        = string
}

variable "enable_container_insights" {
  description = "Enable ECS Container Insights"
  type        = bool
  default     = true
}

variable "enable_fargate_spot" {
  description = "Enable Fargate Spot capacity provider"
  type        = bool
  default     = false
}

variable "enable_service_discovery" {
  description = "Enable ECS Service Discovery"
  type        = bool
  default     = false
}

variable "enable_autoscaling" {
  description = "Enable auto-scaling for ECS services"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention period (days)"
  type        = number
  default     = 14
}

# Backend service configuration
variable "backend_service_name" {
  description = "Name of the backend ECS service"
  type        = string
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

# Frontend service configuration
variable "frontend_service_name" {
  description = "Name of the frontend ECS service"
  type        = string
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

# Auto-scaling configuration
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

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}