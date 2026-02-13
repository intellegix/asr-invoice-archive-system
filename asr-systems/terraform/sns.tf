# ASR Records — SNS Topic for CloudWatch Alarm Notifications
# Wires alarm_actions from cloudwatch.tf to email delivery.

resource "aws_sns_topic" "cloudwatch_alarms" {
  name = "asr-records-alarms-${var.environment}"
}

resource "aws_sns_topic_subscription" "email_alert" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.cloudwatch_alarms.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

