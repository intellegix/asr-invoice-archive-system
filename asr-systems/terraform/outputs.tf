# ASR Records — Consolidated Terraform Outputs

# ---------- RDS ----------

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (host:port)"
  value       = aws_db_instance.asr.endpoint
}

output "rds_db_name" {
  description = "RDS database name"
  value       = aws_db_instance.asr.db_name
}

# ---------- S3 ----------

output "documents_bucket_arn" {
  description = "ARN of the document storage S3 bucket"
  value       = aws_s3_bucket.documents.arn
}

output "documents_bucket_name" {
  description = "Name of the document storage S3 bucket"
  value       = aws_s3_bucket.documents.id
}

output "documents_s3_policy_arn" {
  description = "ARN of the IAM policy for S3 access"
  value       = aws_iam_policy.documents_s3_access.arn
}

# ---------- SNS ----------

output "sns_topic_arn" {
  description = "SNS topic ARN — pass as alarm_sns_topic_arn to CloudWatch alarms"
  value       = aws_sns_topic.cloudwatch_alarms.arn
}
