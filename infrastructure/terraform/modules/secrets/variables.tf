variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "secrets" {
  description = "Map of secrets to store"
  type = object({
    database_password     = string
    redis_auth_token     = string
    elevenlabs_api_key   = string
    openai_api_key       = string
    jwt_secret           = string
    supabase_key         = string
    monitoring_api_key   = string
  })
  sensitive = true
}

variable "database_host" {
  description = "Database host"
  type        = string
}

variable "database_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "database_name" {
  description = "Database name"
  type        = string
}

variable "database_username" {
  description = "Database username"
  type        = string
}

variable "redis_host" {
  description = "Redis host"
  type        = string
}

variable "redis_port" {
  description = "Redis port"
  type        = number
  default     = 6379
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}