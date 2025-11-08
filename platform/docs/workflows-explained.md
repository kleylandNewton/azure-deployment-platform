# GitHub Workflows Explained

This document explains how the platform's CI/CD workflows work and what happens at each step.

---

## Overview

The platform uses two main workflows:

1. **app-validation.yml** - Runs on Pull Requests
2. **app-deployment.yml** - Runs on merge to main

Both workflows are designed with **explainability** as a core feature - every step explains what it's doing and why.

---

## Workflow 1: App Validation (Pull Requests)

**Trigger:** Any PR that changes files in `apps/`

**Purpose:** Validate changes before they're merged and deployed

### Jobs Breakdown

#### 1. Explain Changes 📋

**What it does:**
- Detects which apps changed
- Identifies what type of changes (config, code, Dockerfile)
- Posts a comment explaining the impact of changes

**Why:**
- Users understand what their changes will do
- Shows if deployment will be triggered
- Lists all affected apps

**Example Output:**
```markdown
## 📋 Changes Detected

### 🔄 App: `apps/team-a/customer-api`

**Status:** 📝 Existing app being updated

- ⚙️ **Configuration changed** - Will trigger redeployment
- 🔧 **Backend code changed** - Will rebuild Docker image

**Next Steps:**
1. ✅ Automated validation checks will run below
2. 💰 Cost estimation will be calculated
3. 🔒 Security scans will check for vulnerabilities
4. 👥 Platform team will review if all checks pass
```

#### 2. Validate Configuration ✅

**What it does:**
- Runs `platform/validation/validate.py` on changed app-config.yml files
- Checks against JSON schema
- Verifies Dockerfiles exist if components are enabled
- Warns about high resource allocations

**Why:**
- Catches configuration errors before deployment
- Prevents deployment failures
- Educates users on requirements

**Example Output:**
```markdown
## ✅ Configuration Validation Results

### 📄 `apps/team-a/customer-api/app-config.yml`

❌ **Validation failed**

🔴 **App name must be 3-15 lowercase characters**
   - **Field:** `app.name`
   - **Why this matters:** App name is used in all Azure resource names. Must be DNS-safe.
   - **How to fix:** Change 'MyApp' to 'myapp' or 'my-app'
   - **Documentation:** platform/docs/configuration-reference.md#app-name
```

#### 3. Estimate Costs 💰

**What it does:**
- Runs `scripts/estimate-costs.py` on changed configs
- Calculates monthly Azure costs
- Breaks down costs per resource
- Provides saving tips

**Why:**
- Users know costs before deploying
- Prevents budget surprises
- Encourages cost optimization

**Example Output:**
```markdown
## 💰 Cost Estimation

### 📊 `apps/team-a/customer-api/app-config.yml`

### Monthly Cost Estimate: £45.30

| Resource | Cost | Configuration | Why You Need This |
|----------|------|---------------|-------------------|
| Azure Container Registry | £4.22 | Basic tier | Stores your Docker images. Shared across apps. |
| Backend Container | £28.08 | 1.0 CPU, 1.5GB RAM | Always-on container running your backend API |
| Frontend Container | £13.00 | 0.5 CPU, 1.0GB RAM | Serves your frontend application |

💡 Cost Saving Tips:
- Reduce backend CPU to 0.5 cores to save £14.04/month
- Shared ACR cost across 5 apps = £0.84 per app
```

#### 4. Lint Dockerfiles 🐳

**What it does:**
- Runs Hadolint on changed Dockerfiles
- Checks for best practices
- Warns about security issues

**Why:**
- Ensures Docker images are optimized
- Catches common mistakes
- Improves security

**Example Output:**
```markdown
## 🐳 Dockerfile Best Practices Check

✅ Dockerfiles checked for best practices using Hadolint

**Checked files:**
- `apps/team-a/customer-api/backend/Dockerfile`

**Common best practices:**
- ✅ Use specific image tags (not :latest)
- ✅ Minimize layers by combining RUN commands
- ✅ Use .dockerignore to reduce context size
- ✅ Run as non-root user when possible
```

#### 5. Validation Summary 📊

**What it does:**
- Aggregates results from all checks
- Shows overall pass/fail status
- Provides next steps

**Why:**
- Quick overview of PR status
- Clear action items
- Helps reviewers

**Example Output:**
```markdown
## 📊 Validation Summary

| Check | Status |
|-------|--------|
| 📋 Changes Explained | ✅ Success |
| ✅ Config Validation | ✅ Passed |
| 💰 Cost Estimation | ✅ Complete |
| 🐳 Dockerfile Lint | ✅ Passed |

### ✅ All Critical Checks Passed!

**Next Steps:**
1. Review the detailed comments above
2. Check cost estimates are acceptable
3. Request review from @platform-team
4. Once approved, merge to deploy!
```

---

## Workflow 2: App Deployment (Main Branch)

**Trigger:** Push to main branch that changes `apps/`

**Purpose:** Deploy validated apps to Azure

### Jobs Breakdown

#### 1. Detect Changes 🔍

**What it does:**
- Compares current commit with previous
- Identifies changed app directories
- Creates deployment plan

**Why:**
- Only deploy what changed
- Parallel deployments for multiple apps
- Clear audit trail

**Output:**
```markdown
## 🔍 Deployment Plan

**Apps that will be deployed:**
- 📦 `apps/team-a/customer-api`
- 📦 `apps/team-b/billing-service`

**Deployment started at:** 2025-01-08 14:30:00 UTC
```

#### 2. Deploy (Per App) 🚀

Each changed app gets deployed in parallel. Here's what happens for each:

##### Step 2.1: Parse Configuration

**What it does:**
- Reads app-config.yml
- Extracts app name, team, region, environment
- Validates required fields

**Why:**
- Ensures we have all info needed
- Fails fast if config is invalid
- Documents what's being deployed

##### Step 2.2: Generate Terraform Variables

**What it does:**
- Converts app-config.yml to terraform.tfvars
- Sets all Terraform input variables
- Documents generated config

**Why:**
- Bridge between user config and infrastructure code
- Allows users to use simple YAML instead of Terraform
- Transparent - shows exactly what Terraform will use

##### Step 2.3: Azure Login

**What it does:**
- Authenticates with Azure using service principal
- Uses org-level secrets

**Why:**
- Required to create/modify Azure resources
- Centralized credentials (not per-app)

##### Step 2.4: Terraform Init (Phase 1)

**What it does:**
- Initializes Terraform
- Configures remote state backend
- Uses per-app state file: `{team}/{app-name}.tfstate`

**Why:**
- Each app has isolated state
- Prevents conflicts between apps
- Enables parallel deployments

**Output:**
```markdown
### 🗄️ Terraform State Management

**State Backend:** Azure Blob Storage
**State File:** `team-a/customer-api.tfstate`
**Storage Account:** `stplatformtfstate...`

**Why separate state files?**
- 🛡️ Isolates each app's infrastructure
- ⚡ Enables parallel deployments
- 🔒 Prevents accidental cross-app changes
```

##### Step 2.5: Terraform Plan (Phase 1 - ACR)

**What it does:**
- Plans infrastructure with `create_containers = false`
- Creates only ACR and resource group
- Shows what will be created

**Why:**
- Two-phase deployment prevents chicken-and-egg problem
- ACR must exist before we can push images to it
- Clear visibility into changes

**Output:**
```markdown
### 📝 Phase 1: Infrastructure Plan (ACR)

**Phase 1 Changes:**
- ➕ Creating: 2 resources (ACR, Resource Group)
- 🔄 Updating: 0 resources
- ❌ Destroying: 0 resources
```

##### Step 2.6: Terraform Apply (Phase 1)

**What it does:**
- Creates ACR and resource group
- Waits for creation to complete

**Why:**
- Makes ACR available for image push
- Foundation for app deployment

##### Step 2.7: Build and Push Docker Images

**What it does:**
- Logs into ACR
- Builds backend Docker image (if enabled)
- Builds frontend Docker image (if enabled)
- Pushes images to ACR

**Why:**
- Container instances need images in ACR
- Fresh build ensures latest code is deployed

**Output:**
```markdown
### 🐳 Building Backend Image

✅ Backend image pushed: `acrteamacustomerapi.azurecr.io/app-backend:latest`

### 🎨 Building Frontend Image

✅ Frontend image pushed: `acrteamacustomerapi.azurecr.io/app-frontend:latest`
```

##### Step 2.8: Terraform Plan (Phase 2 - Containers)

**What it does:**
- Restores Terraform state from Phase 1
- Plans infrastructure with `create_containers = true`
- Shows container instances to be created

**Why:**
- Now images exist in ACR, safe to create containers
- Reuses same state (same resource group/ACR)
- Shows exactly what containers will be created

##### Step 2.9: Terraform Apply (Phase 2)

**What it does:**
- Creates container instances
- Pulls images from ACR
- Starts containers

**Why:**
- Deploys your application
- Uses images we just pushed

##### Step 2.10: Health Checks

**What it does:**
- Waits 30 seconds for containers to start
- Attempts HTTP requests to backend/frontend
- Retries up to 10 times with delays

**Why:**
- Verifies deployment succeeded
- Catches startup failures
- Provides confidence app is running

**Output:**
```markdown
### 🏥 Health Checks

**Backend Health Check:**
- ✅ Backend is healthy (attempt 3)
- URL: http://aci-customer-api-backend-dev-xyz123.uksouth.azurecontainer.io:8000

**Frontend Health Check:**
- ✅ Frontend is healthy (attempt 2)
- URL: http://aci-customer-api-frontend-dev-xyz123.uksouth.azurecontainer.io:3000
```

##### Step 2.11: Deployment Summary

**What it does:**
- Aggregates all deployment information
- Provides access URLs
- Links to Azure Portal
- Shows deployment timeline

**Why:**
- One place for all deployment info
- Easy to find URLs
- Quick access to Azure resources

**Output:**
```markdown
## 🎉 Deployment Complete!

### 🌐 Access Your Application

**Backend API:**
- URL: [http://aci-customer-api-backend-dev-xyz123.uksouth.azurecontainer.io:8000](...)
- Try: `curl http://aci-customer-api-backend-dev-xyz123.uksouth.azurecontainer.io:8000/health`

**Frontend:**
- URL: [http://aci-customer-api-frontend-dev-xyz123.uksouth.azurecontainer.io:3000](...)
- Open in browser to see your app

### 📊 Azure Resources

**Resource Group:** `rg-customer-api-dev-xyz123`

[View in Azure Portal](https://portal.azure.com/#@/resource/...)

### ⏱️ Deployment Timeline

- Started: 2025-01-08 14:30:00 UTC
- Duration: ~420 seconds
```

---

## Key Features of Both Workflows

### 1. Explainability

Every step includes:
- **What** it's doing
- **Why** it's necessary
- **What** the output means
- **How** to interpret results

### 2. Error Handling

When things fail:
- Clear error messages
- Context about what was happening
- Suggestions for fixes
- Links to documentation

### 3. Progress Tracking

Throughout deployment:
- Real-time status updates
- Step-by-step progress
- Time estimates
- Success/failure indicators

### 4. Parallel Execution

Multiple apps can:
- Be validated simultaneously
- Deploy in parallel
- Fail independently (fail-fast: false)

### 5. Idempotency

Workflows are safe to re-run:
- Terraform handles state
- Docker builds use caching
- No duplicate resources created

---

## Workflow Triggers Summary

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| app-validation.yml | PR to any branch touching `apps/` | Validate before merge |
| app-deployment.yml | Push to main touching `apps/` | Deploy validated changes |
| app-deployment.yml | Manual (workflow_dispatch) | Deploy specific app on-demand |

---

## Environment Variables

Both workflows use these organization secrets:

| Secret | Purpose | Set In |
|--------|---------|--------|
| `AZURE_CLIENT_ID` | Service principal ID | GitHub org secrets |
| `AZURE_CLIENT_SECRET` | Service principal password | GitHub org secrets |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription | GitHub org secrets |
| `AZURE_TENANT_ID` | Azure AD tenant | GitHub org secrets |
| `TF_STATE_STORAGE_ACCOUNT` | Terraform state storage | GitHub org secrets |
| `TF_STATE_RESOURCE_GROUP` | State storage resource group | GitHub org secrets |

**Why org-level?**
- One place to manage
- Easier to rotate
- All platform repos can use them

---

## Debugging Workflows

### If Validation Fails

1. Check PR comments - they explain what's wrong
2. Fix the issue locally
3. Push changes to same PR branch
4. Validation runs again automatically

### If Deployment Fails

1. Go to Actions tab → Failed workflow
2. Expand failed step
3. Read error message (will explain issue)
4. Common issues:
   - Resource name conflicts → Change app name
   - Quota exceeded → Request increase
   - Permission denied → Check service principal

### If Health Checks Fail

- May be normal (containers still starting)
- Check Azure Portal for container logs
- Verify Dockerfile exposes correct port
- Check app listens on 0.0.0.0 (not localhost)

---

## Customizing Workflows

### Add New Validation Check

Edit `.github/workflows/app-validation.yml`:

```yaml
new-check:
  name: My Custom Check
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Run my check
      run: |
        # Your validation logic

    - name: Post results
      uses: actions/github-script@v7
      # Post comment with results
```

### Add Deployment Step

Edit `.github/workflows/app-deployment.yml`:

```yaml
- name: My Custom Step
  run: |
    echo "### 🎯 My Custom Step" >> $GITHUB_STEP_SUMMARY
    # Your deployment logic
```

### Change Deployment Behavior

Modify terraform.tfvars generation or add new variables.

---

## Best Practices

1. **Always explain in summaries** - Use `>> $GITHUB_STEP_SUMMARY`
2. **Use emoji consistently** - Makes output scannable
3. **Update existing comments** - Don't spam PRs with new comments
4. **Include timing info** - Helps optimize workflow
5. **Fail fast** - Check critical things first
6. **Provide context** - Link to docs, show diffs, explain why

---

## Questions?

- **Workflow not triggering?** Check `paths:` filter in workflow file
- **Want to skip validation?** Can't - it's required for safety
- **Need to deploy without merge?** Use workflow_dispatch with app_path
- **Workflow taking too long?** Check for unnecessary steps or serial execution

See [troubleshooting guide](troubleshooting.md) for more help.
