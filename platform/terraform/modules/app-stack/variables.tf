# Terraform Variables - Populated from app-config.yml

# ============================================================================
# Application Configuration
# ============================================================================

variable "app_name" {
  description = "Base name for the application (from app-config.yml)"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9]{3,15}$", var.app_name))
    error_message = "App name must be 3-15 lowercase letters and numbers only."
  }
}

variable "location" {
  description = "Azure region for deployment"
  type        = string
  default     = "uksouth"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# ============================================================================
# Component Toggles
# ============================================================================

variable "create_containers" {
  description = "Create container instances (set to false for initial deployment)"
  type        = bool
  default     = false
}

variable "backend_enabled" {
  description = "Deploy backend container"
  type        = bool
  default     = true
}

variable "frontend_enabled" {
  description = "Deploy frontend container"
  type        = bool
  default     = true
}

variable "database_enabled" {
  description = "Deploy PostgreSQL database"
  type        = bool
  default     = true
}

# ============================================================================
# Backend Configuration
# ============================================================================

variable "backend_port" {
  description = "Backend container port"
  type        = number
  default     = 8000
}

variable "backend_cpu" {
  description = "Backend CPU cores"
  type        = number
  default     = 1.0
}

variable "backend_memory" {
  description = "Backend memory in GB"
  type        = number
  default     = 1.5
}

# ============================================================================
# Frontend Configuration
# ============================================================================

variable "frontend_port" {
  description = "Frontend container port"
  type        = number
  default     = 3000
}

variable "frontend_cpu" {
  description = "Frontend CPU cores"
  type        = number
  default     = 0.5
}

variable "frontend_memory" {
  description = "Frontend memory in GB"
  type        = number
  default     = 1.0
}

# ============================================================================
# Database Configuration
# ============================================================================

variable "database_sku" {
  description = "Database SKU"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "database_storage_mb" {
  description = "Database storage in MB"
  type        = number
  default     = 32768
}

# ============================================================================
# Environment Variables
# ============================================================================

variable "environment_variables" {
  description = "Custom environment variables for containers"
  type        = map(string)
  default     = {}
}

# ============================================================================
# Tags
# ============================================================================

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default = {
    Project   = "Azure App Template"
    ManagedBy = "Terraform"
  }
}
