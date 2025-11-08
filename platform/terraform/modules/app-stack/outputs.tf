# Terraform Outputs - URLs and Connection Information

# ============================================================================
# Resource Information
# ============================================================================

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "location" {
  description = "Azure region"
  value       = azurerm_resource_group.main.location
}

# ============================================================================
# Container Registry
# ============================================================================

output "acr_login_server" {
  description = "Container registry login server"
  value       = azurerm_container_registry.main.login_server
}

output "acr_name" {
  description = "Container registry name"
  value       = azurerm_container_registry.main.name
}

output "acr_admin_username" {
  description = "Container registry admin username"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "Container registry admin password"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

# ============================================================================
# Backend URLs
# ============================================================================

output "backend_url" {
  description = "Backend application URL"
  value       = var.create_containers && var.backend_enabled ? "http://${azurerm_container_group.backend[0].fqdn}:${var.backend_port}" : "Not deployed"
}

output "backend_fqdn" {
  description = "Backend FQDN"
  value       = var.create_containers && var.backend_enabled ? azurerm_container_group.backend[0].fqdn : "Not deployed"
}

output "backend_ip" {
  description = "Backend IP address"
  value       = var.create_containers && var.backend_enabled ? azurerm_container_group.backend[0].ip_address : "Not deployed"
}

# ============================================================================
# Frontend URLs
# ============================================================================

output "frontend_url" {
  description = "Frontend application URL"
  value       = var.create_containers && var.frontend_enabled ? "http://${azurerm_container_group.frontend[0].fqdn}:${var.frontend_port}" : "Not deployed"
}

output "frontend_fqdn" {
  description = "Frontend FQDN"
  value       = var.create_containers && var.frontend_enabled ? azurerm_container_group.frontend[0].fqdn : "Not deployed"
}

output "frontend_ip" {
  description = "Frontend IP address"
  value       = var.create_containers && var.frontend_enabled ? azurerm_container_group.frontend[0].ip_address : "Not deployed"
}

# ============================================================================
# Database Information
# ============================================================================

output "database_host" {
  description = "Database server FQDN"
  value       = var.database_enabled ? azurerm_postgresql_flexible_server.main[0].fqdn : "Not deployed"
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = var.database_enabled ? azurerm_postgresql_flexible_server_database.main[0].name : "Not deployed"
}

output "database_username" {
  description = "Database admin username"
  value       = var.database_enabled ? azurerm_postgresql_flexible_server.main[0].administrator_login : "Not deployed"
  sensitive   = true
}

output "database_password" {
  description = "Database admin password"
  value       = var.database_enabled ? random_password.db_password[0].result : "Not deployed"
  sensitive   = true
}

output "database_connection_string" {
  description = "Full database connection string"
  value = var.database_enabled ? format(
    "postgresql://%s:%s@%s/%s",
    azurerm_postgresql_flexible_server.main[0].administrator_login,
    random_password.db_password[0].result,
    azurerm_postgresql_flexible_server.main[0].fqdn,
    azurerm_postgresql_flexible_server_database.main[0].name
  ) : "Not deployed"
  sensitive = true
}

# ============================================================================
# Deployment Summary
# ============================================================================

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    app_name         = var.app_name
    environment      = var.environment
    resource_group   = azurerm_resource_group.main.name
    backend_enabled  = var.backend_enabled
    frontend_enabled = var.frontend_enabled
    database_enabled = var.database_enabled
  }
}
