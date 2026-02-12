# ASR Records — CloudWatch Alarms for ECS Services
# Monitors CPU, memory, and 5xx error counts.

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "asr-records-legacy-cluster-dev"
}

variable "backend_service_name" {
  description = "Backend ECS service name"
  type        = string
  default     = "asr-records-backend-service-dev"
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications (leave empty to skip)"
  type        = string
  default     = ""
}

# --------------------------------------------------------------------------
# CPU alarm — fires when average CPU > 80% for 5 minutes
# --------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "backend_cpu_high" {
  alarm_name          = "asr-backend-cpu-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Backend ECS service CPU > 80%"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.backend_service_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
  ok_actions    = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
}

# --------------------------------------------------------------------------
# Memory alarm — fires when average memory > 80% for 5 minutes
# --------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "backend_memory_high" {
  alarm_name          = "asr-backend-memory-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Backend ECS service memory > 80%"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.backend_service_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
  ok_actions    = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
}

# --------------------------------------------------------------------------
# 5xx error alarm — fires when > 10 errors in 5 minutes
# Uses the ALB target group 5xx metric.
# --------------------------------------------------------------------------
variable "alb_arn_suffix" {
  description = "ALB ARN suffix (e.g. app/asr-records-alb/1234567890)"
  type        = string
  default     = ""
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix"
  type        = string
  default     = ""
}

resource "aws_cloudwatch_metric_alarm" "backend_5xx_errors" {
  count               = var.alb_arn_suffix != "" && var.target_group_arn_suffix != "" ? 1 : 0
  alarm_name          = "asr-backend-5xx-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Backend 5xx errors > 10 in 5 min"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.target_group_arn_suffix
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
  ok_actions    = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
}
