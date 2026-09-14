variable "owner_initials" {
  description = "Your 2-4 lowercase initials. Same convention as the rest of Week 8."
  type        = string
  default     = "phr"
}

variable "vpc_id" {
  description = "VPC the staging service runs in."
  type        = string
  default     = "vpc-00000000000000000"
}

variable "private_subnet_ids" {
  description = "Private subnets for the Fargate tasks."
  type        = list(string)
  default     = ["subnet-00000000000000001", "subnet-00000000000000002"]
}

variable "listener_arn" {
  description = "ARN of the ALB production listener."
  type        = string
  default     = "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/phr/0/0"
}
