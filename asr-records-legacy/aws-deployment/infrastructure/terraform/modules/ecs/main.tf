# ASR Records Legacy - ECS Module
# Modular ECS cluster and service configuration

###########################################
# ECS Cluster
###########################################

resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"

      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.cluster.name
      }
    }
  }

  tags = var.tags
}

# Cluster logging
resource "aws_cloudwatch_log_group" "cluster" {
  name              = "/ecs/${var.cluster_name}-exec"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

###########################################
# ECS Capacity Providers (Optional)
###########################################

resource "aws_ecs_cluster_capacity_providers" "main" {
  count = var.enable_fargate_spot ? 1 : 0

  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = var.enable_fargate_spot ? ["FARGATE", "FARGATE_SPOT"] : ["FARGATE"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = var.enable_fargate_spot ? 50 : 100
    capacity_provider = "FARGATE"
  }

  dynamic "default_capacity_provider_strategy" {
    for_each = var.enable_fargate_spot ? [1] : []
    content {
      weight            = 50
      capacity_provider = "FARGATE_SPOT"
    }
  }
}

###########################################
# Service Discovery (Optional)
###########################################

resource "aws_service_discovery_private_dns_namespace" "main" {
  count = var.enable_service_discovery ? 1 : 0

  name        = "${var.cluster_name}.local"
  description = "Service discovery namespace for ${var.cluster_name}"
  vpc         = var.vpc_id

  tags = var.tags
}

###########################################
# Auto Scaling Target
###########################################

resource "aws_appautoscaling_target" "backend" {
  count = var.enable_autoscaling ? 1 : 0

  max_capacity       = var.backend_max_capacity
  min_capacity       = var.backend_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${var.backend_service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  depends_on = [aws_ecs_cluster.main]
}

resource "aws_appautoscaling_target" "frontend" {
  count = var.enable_autoscaling ? 1 : 0

  max_capacity       = var.frontend_max_capacity
  min_capacity       = var.frontend_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${var.frontend_service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  depends_on = [aws_ecs_cluster.main]
}

# CPU-based auto scaling policy for backend
resource "aws_appautoscaling_policy" "backend_cpu" {
  count = var.enable_autoscaling ? 1 : 0

  name               = "${var.backend_service_name}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend[0].resource_id
  scalable_dimension = aws_appautoscaling_target.backend[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend[0].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = var.autoscaling_target_cpu
    scale_in_cooldown  = var.scale_down_cooldown
    scale_out_cooldown = var.scale_up_cooldown

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# Memory-based auto scaling policy for backend
resource "aws_appautoscaling_policy" "backend_memory" {
  count = var.enable_autoscaling ? 1 : 0

  name               = "${var.backend_service_name}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend[0].resource_id
  scalable_dimension = aws_appautoscaling_target.backend[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend[0].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = var.autoscaling_target_memory
    scale_in_cooldown  = var.scale_down_cooldown
    scale_out_cooldown = var.scale_up_cooldown

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
  }
}

# CPU-based auto scaling policy for frontend
resource "aws_appautoscaling_policy" "frontend_cpu" {
  count = var.enable_autoscaling ? 1 : 0

  name               = "${var.frontend_service_name}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend[0].resource_id
  scalable_dimension = aws_appautoscaling_target.frontend[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend[0].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = var.autoscaling_target_cpu
    scale_in_cooldown  = var.scale_down_cooldown
    scale_out_cooldown = var.scale_up_cooldown

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}