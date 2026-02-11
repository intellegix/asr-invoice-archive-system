# ASR Records Legacy - ECS Module Outputs

output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "cluster_log_group_name" {
  description = "Name of the CloudWatch log group for cluster execution"
  value       = aws_cloudwatch_log_group.cluster.name
}

output "service_discovery_namespace_id" {
  description = "ID of the service discovery namespace"
  value       = var.enable_service_discovery ? aws_service_discovery_private_dns_namespace.main[0].id : null
}

output "service_discovery_namespace_name" {
  description = "Name of the service discovery namespace"
  value       = var.enable_service_discovery ? aws_service_discovery_private_dns_namespace.main[0].name : null
}

output "backend_autoscaling_target_resource_id" {
  description = "Resource ID for backend auto-scaling target"
  value       = var.enable_autoscaling ? aws_appautoscaling_target.backend[0].resource_id : null
}

output "frontend_autoscaling_target_resource_id" {
  description = "Resource ID for frontend auto-scaling target"
  value       = var.enable_autoscaling ? aws_appautoscaling_target.frontend[0].resource_id : null
}

output "backend_cpu_scaling_policy_arn" {
  description = "ARN of the backend CPU scaling policy"
  value       = var.enable_autoscaling ? aws_appautoscaling_policy.backend_cpu[0].arn : null
}

output "backend_memory_scaling_policy_arn" {
  description = "ARN of the backend memory scaling policy"
  value       = var.enable_autoscaling ? aws_appautoscaling_policy.backend_memory[0].arn : null
}

output "frontend_cpu_scaling_policy_arn" {
  description = "ARN of the frontend CPU scaling policy"
  value       = var.enable_autoscaling ? aws_appautoscaling_policy.frontend_cpu[0].arn : null
}