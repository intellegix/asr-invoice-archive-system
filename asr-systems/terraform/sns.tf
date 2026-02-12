# ASR Records — SNS Topic for CloudWatch Alarm Notifications
# Wires alarm_actions from cloudwatch.tf to email delivery.

variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = ""
}

resource "aws_sns_topic" "cloudwatch_alarms" {
  name = "asr-records-alarms-${var.environment}"
}

resource "aws_sns_topic_subscription" "email_alert" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.cloudwatch_alarms.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

output "sns_topic_arn" {
  description = "SNS topic ARN — pass as alarm_sns_topic_arn to cloudwatch.tf"
  value       = aws_sns_topic.cloudwatch_alarms.arn
}
