# Terraform Backend Configuration
#
# This configures where Terraform stores its state files.
# State files track what infrastructure exists in Azure.
#
# Why Azure Blob Storage?
# - Built-in state locking (prevents concurrent modifications)
# - Versioning support (can recover from mistakes)
# - Secure (encrypted at rest)
# - Cost-effective (~£0.01/month for state storage)
#
# State Organization:
# Each app gets its own state file: {team}/{app-name}.tfstate
# This prevents one app's changes from affecting others.
#
# Setup Instructions:
# 1. Create Azure storage account (see platform/docs/setup-guide.md)
# 2. Configure these values as GitHub secrets:
#    - TF_STATE_STORAGE_ACCOUNT
#    - TF_STATE_RESOURCE_GROUP
# 3. Terraform init will use these values dynamically in CI/CD

terraform {
  backend "azurerm" {
    # These values will be provided dynamically via terraform init flags
    # -backend-config="key={team}/{app-name}.tfstate"
    # -backend-config="storage_account_name=${TF_STATE_STORAGE_ACCOUNT}"
    # -backend-config="resource_group_name=${TF_STATE_RESOURCE_GROUP}"
    # -backend-config="container_name=tfstate"

    # Configuration is intentionally minimal here
    # Values are set at runtime in CI/CD workflows
  }
}

# Why this approach?
# - Allows different state files per app (blast radius control)
# - Centralized storage (one place to backup/audit)
# - Secure (no state files committed to git)
# - Scalable (can have hundreds of apps)
