# Platform Setup Guide

This guide walks you through setting up the Azure Deployment Platform from scratch.

**Time required:** 30 minutes
**Prerequisites:** Azure subscription, GitHub organization

---

## Phase 1: Azure Infrastructure Setup

### Step 1: Create Terraform State Storage

Terraform needs a place to store its state files. We use Azure Blob Storage.

**Run in Azure Cloud Shell:**

```bash
# Variables
LOCATION="uksouth"
RG_NAME="rg-platform-terraform-state"
STORAGE_ACCOUNT_NAME="stplatformtfstate$(date +%s)"  # Must be globally unique

# Create resource group
az group create \
  --name $RG_NAME \
  --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RG_NAME \
  --location $LOCATION \
  --sku Standard_LRS \
  --encryption-services blob \
  --allow-blob-public-access false

# Enable versioning (for state recovery)
az storage account blob-service-properties update \
  --account-name $STORAGE_ACCOUNT_NAME \
  --resource-group $RG_NAME \
  --enable-versioning true

# Create container for state files
az storage container create \
  --name tfstate \
  --account-name $STORAGE_ACCOUNT_NAME \
  --auth-mode login

# IMPORTANT: Save these values!
echo "======================================"
echo "Save these values for GitHub Secrets:"
echo "======================================"
echo "TF_STATE_STORAGE_ACCOUNT=$STORAGE_ACCOUNT_NAME"
echo "TF_STATE_RESOURCE_GROUP=$RG_NAME"
echo "======================================"
```

**Why we do this:**
- Terraform state tracks what resources exist in Azure
- Storing state in Azure prevents conflicts when multiple people deploy
- Versioning lets us recover if state gets corrupted
- Each app gets its own state file for safety

---

### Step 2: Create Service Principal

The platform needs credentials to create Azure resources.

**Run in Azure Cloud Shell:**

```bash
# Create service principal with contributor role
az ad sp create-for-rbac \
  --name "github-actions-platform-$(date +%s)" \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv) \
  --json-auth

# Output will look like:
# {
#   "clientId": "xxx",
#   "clientSecret": "xxx",
#   "subscriptionId": "xxx",
#   "tenantId": "xxx"
# }

# IMPORTANT: Save all four values for GitHub Secrets!
```

**What is this?**
- Service principal = Azure identity for automation
- Contributor role = Can create/modify resources
- Scoped to subscription = Can't affect other subscriptions

**Security note:**
- Treat these credentials like passwords
- Only store in GitHub Secrets (encrypted)
- Rotate periodically (every 90 days)

---

## Phase 2: GitHub Setup

### Step 3: Create GitHub Repository

```bash
cd /Users/kitleyland/Documents/Coding_projects/azure-deployment-platform

# Initialize git repository
git init

# Create initial commit
git add .
git commit -m "Initial platform setup

- Repository structure
- Validation framework
- Cost estimation
- ADRs and documentation
- Terraform modules

🤖 Generated with Claude Code"

# Create GitHub repository
gh repo create azure-deployment-platform --public --source=. --push

# Or manually:
# 1. Go to GitHub → New Repository
# 2. Name: azure-deployment-platform
# 3. Push code:
#    git remote add origin https://github.com/YOUR_ORG/azure-deployment-platform.git
#    git push -u origin main
```

---

### Step 4: Configure GitHub Organization Secrets

**Why organization-level secrets?**
- One place to manage credentials (not per-repo)
- All platform repos can use them
- Easier to rotate
- More secure (centralized audit)

**Setup:**

1. **Go to GitHub Organization Settings:**
   - https://github.com/organizations/YOUR_ORG/settings/secrets/actions

2. **Click "New organization secret"**

3. **Add these 6 secrets:**

| Secret Name | Value | Source |
|------------|-------|--------|
| `AZURE_CLIENT_ID` | From Step 2 output | Service principal `clientId` |
| `AZURE_CLIENT_SECRET` | From Step 2 output | Service principal `clientSecret` |
| `AZURE_SUBSCRIPTION_ID` | From Step 2 output | Service principal `subscriptionId` |
| `AZURE_TENANT_ID` | From Step 2 output | Service principal `tenantId` |
| `TF_STATE_STORAGE_ACCOUNT` | From Step 1 output | Storage account name |
| `TF_STATE_RESOURCE_GROUP` | From Step 1 output | Resource group name (rg-platform-terraform-state) |

4. **Set repository access:**
   - Select "Selected repositories"
   - Add `azure-deployment-platform`

**Verification:**
```bash
# Check secrets are configured (won't show values, just names)
gh secret list --org YOUR_ORG
```

---

### Step 5: Configure Repository Settings

**Branch Protection:**

1. Go to repository Settings → Branches
2. Add rule for `main` branch:
   - ✅ Require pull request before merging
   - ✅ Require approvals (1)
   - ✅ Require status checks to pass
   - ✅ Require conversation resolution
   - ✅ Include administrators

**Why?**
- Prevents accidental direct pushes to main
- Ensures all changes are reviewed
- Validates changes before merge
- Creates audit trail

**CODEOWNERS:**

The `.github/CODEOWNERS` file is already configured. Update it with your team:

```bash
# Edit .github/CODEOWNERS
# Replace @platform-team with your GitHub team/username
```

---

## Phase 3: Test the Platform

### Step 6: Migrate Pilot App

Let's migrate the azure-test-deployment app as a pilot.

```bash
# Create pilot app directory
mkdir -p apps/pilot/testapp

# Copy files from azure-test-deployment
cp -r /path/to/azure-test-deployment/backend apps/pilot/testapp/
cp -r /path/to/azure-test-deployment/frontend apps/pilot/testapp/
cp /path/to/azure-test-deployment/app-config.yml apps/pilot/testapp/

# Update app-config.yml
cat > apps/pilot/testapp/app-config.yml <<EOF
app:
  name: "testapp"
  team: "pilot"
  region: "uksouth"
  description: "Pilot app for testing platform"

components:
  backend:
    enabled: true
    port: 8000
    cpu: 1.0
    memory: 1.5

  frontend:
    enabled: true
    port: 3000
    cpu: 0.5
    memory: 1.0

  database:
    enabled: false

environment: "dev"
EOF

# Update registry
cat >> apps/_registry.yml <<EOF
  - name: testapp
    team: pilot
    path: apps/pilot/testapp
    status: active
    created: "$(date +%Y-%m-%d)"
    environment: dev
    description: "Pilot app migrated from azure-test-deployment"
EOF
```

---

### Step 7: Test Validation Locally

Before creating a PR, test validation works:

```bash
# Install dependencies
pip install jsonschema pyyaml

# Run validation
python platform/validation/validate.py apps/pilot/testapp/app-config.yml

# Should output JSON with is_valid: true

# Test cost estimation
python scripts/estimate-costs.py apps/pilot/testapp/app-config.yml

# Should output cost breakdown
```

---

### Step 8: Create Test PR

```bash
# Create branch
git checkout -b add-pilot-app

# Commit changes
git add apps/pilot/testapp apps/_registry.yml
git commit -m "Add pilot app for testing

- Migrated from azure-test-deployment
- Backend (FastAPI) + Frontend (Express)
- For testing platform workflows"

# Push and create PR
git push origin add-pilot-app
gh pr create --title "Add pilot app" --body "Testing platform with pilot app"
```

**What should happen:**
1. PR validation workflow runs automatically
2. Comments posted with:
   - ✅ Validation results
   - 💰 Cost estimate
   - 🐳 Dockerfile checks
3. You review the output
4. If all passes, merge PR
5. Deployment workflow runs automatically
6. App deploys to Azure!

---

## Phase 4: Verify Deployment

### Step 9: Check Deployment Status

After merging PR:

1. **Go to Actions tab** in GitHub
2. **Click latest "Deploy Applications" run**
3. **Check workflow summary** for:
   - Backend URL
   - Frontend URL
   - Resource group name
4. **Test the app:**
   ```bash
   curl <backend-url>/health
   # Should return 200 OK
   ```

5. **Verify in Azure Portal:**
   - Go to Resource Groups
   - Find `rg-testapp-dev-*`
   - Should see:
     - Container Registry
     - 2x Container Instances
     - All resources tagged properly

---

## Phase 5: Onboard Your Team

### Step 10: Create Onboarding Documentation

Share this with your teams:

**For new apps:**
1. Create branch: `git checkout -b add-my-app`
2. Create folder: `mkdir -p apps/my-team/my-app`
3. Add code and app-config.yml
4. Update apps/_registry.yml
5. Create PR
6. Wait for validation
7. Platform team reviews
8. Merge → automatic deployment!

**For updates:**
1. Edit code in `apps/my-team/my-app/`
2. Create PR
3. Merge → automatic redeployment!

---

## Troubleshooting

### Validation Fails

**Problem:** JSON schema validation errors

**Solution:**
```bash
# Check your app-config.yml syntax
python platform/validation/validate.py apps/your-team/your-app/app-config.yml

# Read the error message carefully - it explains:
# - What's wrong
# - Why it matters
# - How to fix it
```

---

### Deployment Fails

**Problem:** Terraform errors during deployment

**Check:**
1. Go to Actions → Failed workflow
2. Expand "Terraform Apply" step
3. Read error message

**Common issues:**
- Resource name already exists → Change app name
- Quota exceeded → Request quota increase
- Permission denied → Check service principal has Contributor role

---

### Can't Access Deployed App

**Problem:** URLs don't respond

**Check:**
1. Container started successfully (check Azure Portal)
2. Wait 2-3 minutes for containers to fully start
3. Check health endpoint: `curl <url>/health`
4. View container logs in Azure Portal

---

## Next Steps

Now that the platform is set up:

1. ✅ **Document team onboarding** → Create `platform/docs/team-onboarding.md`
2. ✅ **Set up monitoring** → Add Azure Monitor dashboards
3. ✅ **Configure alerts** → Cost alerts, deployment failures
4. ✅ **Add more teams** → Update CODEOWNERS, registry
5. ✅ **Improve workflows** → Add more validation checks

See [platform/docs/decision-log.md](decision-log.md) for architectural decisions and future enhancements.

---

## Support

**Questions?** Create GitHub issue
**Security concerns?** Contact platform team directly
**Feature requests?** Add to GitHub discussions

---

## Summary Checklist

Setup complete when you have:

- [ ] Azure storage account for Terraform state
- [ ] Service principal with Contributor role
- [ ] GitHub repository created
- [ ] 6 organization secrets configured
- [ ] Branch protection enabled on main
- [ ] CODEOWNERS updated with your team
- [ ] Pilot app migrated and deployed
- [ ] Validation tested locally
- [ ] First PR merged successfully
- [ ] App accessible at provided URLs

**Congratulations!** Your platform is ready for teams to use. 🎉
