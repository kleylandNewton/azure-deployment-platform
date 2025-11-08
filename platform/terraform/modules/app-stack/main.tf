# Azure App Template - Main Terraform Configuration
# This handles ALL infrastructure with centralized naming conventions

terraform {
  required_version = ">= 1.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Backend configuration for state storage
  # Uncomment and configure for production use
  # backend "azurerm" {
  #   resource_group_name  = "rg-terraform-state"
  #   storage_account_name = "sttfstate"
  #   container_name       = "tfstate"
  #   key                  = "app.tfstate"
  # }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# ============================================================================
# Random Suffix for Unique Naming
# ============================================================================

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
  numeric = true
}

# ============================================================================
# Local Variables - Centralized Naming Convention
# ============================================================================

locals {
  # Unique suffix combining environment and random string
  unique_suffix = "${var.environment}-${random_string.suffix.result}"

  # Standardized naming convention (controlled centrally)
  resource_group_name = "rg-${var.app_name}-${local.unique_suffix}"
  acr_name           = "acr${var.app_name}${replace(local.unique_suffix, "-", "")}"
  backend_name       = "aci-${var.app_name}-backend-${local.unique_suffix}"
  frontend_name      = "aci-${var.app_name}-frontend-${local.unique_suffix}"
  db_server_name     = "psql-${var.app_name}-${local.unique_suffix}"
  db_name            = "${var.app_name}_db"

  # URLs (will be generated after deployment)
  backend_fqdn       = "${local.backend_name}.${var.location}.azurecontainer.io"
  frontend_fqdn      = var.frontend_enabled ? "${local.frontend_name}.${var.location}.azurecontainer.io" : ""

  # Common tags
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      ManagedBy   = "Terraform"
      AppName     = var.app_name
      DeployedAt  = timestamp()
    }
  )
}

# ============================================================================
# Resource Group
# ============================================================================

resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# ============================================================================
# Azure Container Registry
# ============================================================================

resource "azurerm_container_registry" "main" {
  name                = local.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = local.common_tags
}

# ============================================================================
# PostgreSQL Database (Optional)
# ============================================================================

resource "random_password" "db_password" {
  count   = var.database_enabled ? 1 : 0
  length  = 32
  special = true
}

resource "azurerm_postgresql_flexible_server" "main" {
  count               = var.database_enabled ? 1 : 0
  name                = local.db_server_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  administrator_login    = "sqladmin"
  administrator_password = random_password.db_password[0].result

  sku_name   = var.database_sku
  storage_mb = var.database_storage_mb
  version    = "13"

  backup_retention_days        = 7
  geo_redundant_backup_enabled = false

  tags = local.common_tags
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  count     = var.database_enabled ? 1 : 0
  name      = local.db_name
  server_id = azurerm_postgresql_flexible_server.main[0].id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Allow Azure services to access database
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  count            = var.database_enabled ? 1 : 0
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.main[0].id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# ============================================================================
# Backend Container Instance
# ============================================================================

resource "azurerm_container_group" "backend" {
  count               = var.create_containers && var.backend_enabled ? 1 : 0
  name                = local.backend_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  dns_name_label      = local.backend_name

  image_registry_credential {
    server   = azurerm_container_registry.main.login_server
    username = azurerm_container_registry.main.admin_username
    password = azurerm_container_registry.main.admin_password
  }

  container {
    name   = "backend"
    image  = "${azurerm_container_registry.main.login_server}/app-backend:latest"
    cpu    = var.backend_cpu
    memory = var.backend_memory

    ports {
      port     = var.backend_port
      protocol = "TCP"
    }

    environment_variables = merge(
      var.environment_variables,
      {
        PORT        = tostring(var.backend_port)
        ENVIRONMENT = var.environment
      },
      # Database connection if enabled
      var.database_enabled ? {
        DATABASE_HOST     = azurerm_postgresql_flexible_server.main[0].fqdn
        DATABASE_NAME     = local.db_name
        DATABASE_USER     = "sqladmin"
        DATABASE_PASSWORD = random_password.db_password[0].result
      } : {}
    )
  }

  tags = local.common_tags
}

# ============================================================================
# Frontend Container Instance (Optional)
# ============================================================================

resource "azurerm_container_group" "frontend" {
  count               = var.create_containers && var.frontend_enabled ? 1 : 0
  name                = local.frontend_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  dns_name_label      = local.frontend_name

  image_registry_credential {
    server   = azurerm_container_registry.main.login_server
    username = azurerm_container_registry.main.admin_username
    password = azurerm_container_registry.main.admin_password
  }

  container {
    name   = "frontend"
    image  = "${azurerm_container_registry.main.login_server}/app-frontend:latest"
    cpu    = var.frontend_cpu
    memory = var.frontend_memory

    ports {
      port     = var.frontend_port
      protocol = "TCP"
    }

    environment_variables = merge(
      var.environment_variables,
      {
        PORT             = tostring(var.frontend_port)
        BACKEND_URL      = "http://${local.backend_fqdn}:${var.backend_port}"
        NEXT_PUBLIC_API_URL = "http://${local.backend_fqdn}:${var.backend_port}"
      }
    )
  }

  tags = local.common_tags
}
