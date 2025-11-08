# Apps Directory

This directory contains all applications deployed via the platform.

## Structure

```
apps/
├── _registry.yml          # Master list of all apps
├── team-name/
│   └── app-name/
│       ├── app-config.yml # Configuration (required)
│       ├── backend/       # Backend code (optional)
│       │   ├── Dockerfile
│       │   └── ...
│       └── frontend/      # Frontend code (optional)
│           ├── Dockerfile
│           └── ...
```

## Adding a New App

### 1. Create Directory Structure

```bash
mkdir -p apps/YOUR_TEAM/YOUR_APP
```

### 2. Create app-config.yml

```yaml
app:
  name: "your-app"        # 3-15 chars, lowercase, letters/numbers/hyphens
  team: "your-team"       # Your team name
  region: "uksouth"       # Azure region
  description: "What your app does"

components:
  backend:
    enabled: true         # Deploy backend?
    port: 8000           # Port backend listens on
    cpu: 1.0             # CPU cores (affects cost)
    memory: 1.5          # Memory in GB (affects cost)

  frontend:
    enabled: true         # Deploy frontend?
    port: 3000
    cpu: 0.5
    memory: 1.0

  database:
    enabled: false        # Deploy database?
    type: "postgresql"    # postgresql or mysql
    tier: "Basic"         # Basic, GeneralPurpose, MemoryOptimized
    storage_mb: 32768     # 32GB

environment: "dev"        # dev, staging, or prod
```

### 3. Add Your Code

**Backend (if enabled):**
```bash
# Add your backend code
cp -r ~/my-backend-code/* apps/YOUR_TEAM/YOUR_APP/backend/

# Ensure Dockerfile exists
ls apps/YOUR_TEAM/YOUR_APP/backend/Dockerfile
```

**Frontend (if enabled):**
```bash
# Add your frontend code
cp -r ~/my-frontend-code/* apps/YOUR_TEAM/YOUR_APP/frontend/

# Ensure Dockerfile exists
ls apps/YOUR_TEAM/YOUR_APP/frontend/Dockerfile
```

### 4. Update Registry

Edit `apps/_registry.yml`:

```yaml
apps:
  # ... existing apps ...

  - name: your-app
    team: your-team
    path: apps/your-team/your-app
    status: active
    created: "2025-01-08"  # Today's date
    environment: dev
    description: "Brief description"
```

### 5. Test Locally

```bash
# Validate configuration
python platform/validation/validate.py apps/YOUR_TEAM/YOUR_APP/app-config.yml

# Estimate costs
python scripts/estimate-costs.py apps/YOUR_TEAM/YOUR_APP/app-config.yml

# Test Docker builds
docker build apps/YOUR_TEAM/YOUR_APP/backend -t test:backend
docker build apps/YOUR_TEAM/YOUR_APP/frontend -t test:frontend
```

### 6. Create Pull Request

```bash
git checkout -b add-your-app
git add apps/YOUR_TEAM/YOUR_APP apps/_registry.yml
git commit -m "Add your-app

- Backend: Brief description
- Frontend: Brief description
- Estimated cost: £XX/month"

git push origin add-your-app
gh pr create
```

### 7. Wait for Validation

Automated checks will run and post comments on your PR with:
- ✅ Configuration validation results
- 💰 Cost estimates
- 🐳 Dockerfile linting
- 📊 Overall summary

### 8. Merge to Deploy

Once approved and merged:
- Deployment runs automatically
- Check Actions tab for progress
- Get URLs from workflow summary

## Updating an Existing App

### Update Code

```bash
git checkout -b update-your-app

# Update your code
vim apps/YOUR_TEAM/YOUR_APP/backend/main.py

git add apps/YOUR_TEAM/YOUR_APP/
git commit -m "Update feature X"
git push origin update-your-app
gh pr create
```

Merge → Automatic redeployment!

### Update Configuration

```bash
git checkout -b update-your-app-config

# Edit config
vim apps/YOUR_TEAM/YOUR_APP/app-config.yml
# Example: Change cpu from 1.0 to 2.0

git add apps/YOUR_TEAM/YOUR_APP/app-config.yml
git commit -m "Increase CPU allocation for better performance"
git push origin update-your-app-config
gh pr create
```

PR will show:
- Configuration diff
- New cost estimate
- What will change in infrastructure

## Configuration Reference

### App Settings

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `app.name` | Yes | App identifier (3-15 chars, lowercase) | `customer-api` |
| `app.team` | Yes | Team name (for cost allocation) | `team-a` |
| `app.region` | No | Azure region (default: uksouth) | `uksouth` |
| `app.description` | No | Brief description | `Customer management API` |

### Backend Settings

| Field | Required | Description | Default |
|-------|----------|-------------|---------|
| `components.backend.enabled` | Yes | Deploy backend? | - |
| `components.backend.port` | No | Port backend listens on | 8000 |
| `components.backend.cpu` | No | CPU cores (0.5-4.0) | 1.0 |
| `components.backend.memory` | No | Memory in GB (0.5-8.0) | 1.5 |
| `components.backend.directory` | No | Path to backend code | `./backend` |

### Frontend Settings

Same as backend, but defaults:
- `port`: 3000
- `cpu`: 0.5
- `memory`: 1.0
- `directory`: `./frontend`

### Database Settings

| Field | Required | Description | Options |
|-------|----------|-------------|---------|
| `components.database.enabled` | Yes | Deploy database? | true/false |
| `components.database.type` | No | Database type | `postgresql`, `mysql` |
| `components.database.tier` | No | Performance tier | `Basic`, `GeneralPurpose`, `MemoryOptimized` |
| `components.database.storage_mb` | No | Storage size | 5120-1048576 (5GB-1TB) |

## Cost Estimates

Typical monthly costs (Azure UK South):

| Configuration | Monthly Cost |
|--------------|-------------|
| Backend only (1 core, 1.5GB) | ~£30 |
| Frontend only (0.5 core, 1GB) | ~£15 |
| Both (default config) | ~£45 |
| + PostgreSQL Basic | +£25 |
| + PostgreSQL GeneralPurpose | +£55 |

**Tips to reduce costs:**
- Disable database for dev/test
- Use lower CPU/memory for non-prod
- Destroy when not in use

## Dockerfile Requirements

### Backend Dockerfile

Must:
- ✅ Expose the port specified in app-config.yml
- ✅ Run application on 0.0.0.0 (not localhost)
- ✅ Include health check endpoint
- ✅ Follow security best practices

Example:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

Must:
- ✅ Expose the port specified in app-config.yml
- ✅ Serve on 0.0.0.0
- ✅ Include production build

Example:
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --production

COPY . .

EXPOSE 3000
CMD ["node", "server.js"]
```

## Validation Rules

Your PR must pass:

### Configuration Validation
- ✅ Valid YAML syntax
- ✅ Matches JSON schema
- ✅ App name is unique
- ✅ Team is registered
- ✅ Required Dockerfiles exist

### Dockerfile Linting
- ✅ Hadolint rules pass
- ✅ No critical security issues
- ✅ Best practices followed

### Cost Check
- ⚠️ Warning if > £100/month
- ℹ️ Estimate posted in PR

## Common Issues

### "App name already exists"

**Problem:** Another app uses that name

**Fix:**
```yaml
app:
  name: "customer-api-v2"  # Make it unique
```

### "Backend enabled but Dockerfile not found"

**Problem:** Missing Dockerfile

**Fix:**
```bash
# Create Dockerfile
touch apps/YOUR_TEAM/YOUR_APP/backend/Dockerfile
# Add Dockerfile content
```

### "Configuration validation failed"

**Problem:** Invalid app-config.yml

**Fix:**
- Read the error message (it explains what's wrong and how to fix)
- Test locally: `python platform/validation/validate.py apps/YOUR_TEAM/YOUR_APP/app-config.yml`

### "Cost estimate very high"

**Problem:** Resource allocation too high

**Fix:**
```yaml
components:
  backend:
    cpu: 0.5      # Reduce from 2.0
    memory: 1.0   # Reduce from 4.0
```

## Team Ownership

Teams can only modify their own apps (enforced by CODEOWNERS):

```
/apps/team-a/  @team-a-leads
/apps/team-b/  @team-b-leads
```

All app-config.yml changes require platform team approval:

```
/apps/**/app-config.yml  @platform-team
```

## Registry Format

`_registry.yml` tracks all deployed apps:

```yaml
apps:
  - name: "app-identifier"
    team: "team-name"
    path: "apps/team-name/app-name"
    status: active | inactive | archived
    created: "2025-01-08"
    environment: dev | staging | prod
    description: "Brief description"
```

**Status meanings:**
- `active`: Currently deployed and running
- `inactive`: Exists but not deployed
- `archived`: Historical, scheduled for removal

## Getting Help

- **Validation errors?** Read the error message (explains fix)
- **Cost questions?** Check cost estimate in PR
- **Deployment issues?** See Actions workflow logs
- **General questions?** Ask @platform-team

## Best Practices

1. **Start small** - Deploy with minimal resources, scale up if needed
2. **Test locally** - Build Docker images before creating PR
3. **Read error messages** - They explain what's wrong and how to fix
4. **Check costs** - Review estimate before merging
5. **Use descriptive names** - Makes resources easy to identify
6. **Tag resources** - Use `tags` field in app-config.yml

## Examples

See `pilot/testapp/` for a working example with:
- ✅ Valid app-config.yml
- ✅ Working backend Dockerfile
- ✅ Working frontend Dockerfile
- ✅ Registered in _registry.yml

Copy and modify for your app!

---

**Ready to deploy?** Create your app directory and follow the steps above!
