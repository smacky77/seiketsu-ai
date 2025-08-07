variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the frontend"
  type        = string
}

variable "api_domain_name" {
  description = "API domain name for backend origin"
  type        = string
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for CloudFront"
  type        = string
}

variable "waf_web_acl_arn" {
  description = "ARN of WAF Web ACL"
  type        = string
  default     = null
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
  
  validation {
    condition     = contains(["PriceClass_All", "PriceClass_200", "PriceClass_100"], var.price_class)
    error_message = "Price class must be PriceClass_All, PriceClass_200, or PriceClass_100."
  }
}

variable "create_s3_bucket" {
  description = "Whether to create S3 bucket for static assets"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}