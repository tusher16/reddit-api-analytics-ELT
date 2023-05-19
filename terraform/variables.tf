variable "db_password" {
  description = "Password for Redshift master DB user"
  type        = string
  default     = "h9!L*31rs02"
}


variable "s3_bucket" {
  description = "Bucket name for S3"
  type        = string
  default     = "tusher-reddit-bucket"
}


variable "aws_region" {
  description = "Region for AWS"
  type        = string
  default     = "eu-central-1"
}