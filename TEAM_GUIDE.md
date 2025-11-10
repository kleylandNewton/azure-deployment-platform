# Azure Deployment Platform - Quick Start Guide

## What is This?

A **self-service platform** for deploying applications to Azure. You add your app code and a config file, create a PR, and the platform handles validation, cost estimation, and deployment automatically.

## Architecture Overview

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture diagrams and design decisions.

**Quick summary:**
- **Monorepo:** All apps live in `apps/TEAM/APP/`
- **Config-driven:** Describe what you want in YAML
- **PR validation:** Automated checks before deployment
- **Auto-deploy:** Merge PR → deploy to Azure
- **Two-phase deployment:** ACR creation → image building → container deployment

## Why Use This Platform?

✅ **No Azure credentials needed** - Platform manages them
✅ **Validate before deploying** - Catch errors in PR
✅ **See costs upfront** - Monthly estimates before merging
✅ **No Terraform knowledge required** - Just write YAML
✅ **Fast feedback** - Automated checks in seconds

## Quick Start: Deploy an App in 10 Minutes

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_ORG/azure-deployment-platform.git
cd azure-deployment-platform
```

### 2. Create App Structure
```bash
mkdir -p apps/YOUR_TEAM/YOUR_APP/backend
```

### 3. Add Configuration
```bash
cat > apps/YOUR_TEAM/YOUR_APP/app-config.yml <<EOF
app:
  name: "your-app"
  team: "your-team"
  region: "uksouth"
  description: "Brief description"

components:
  backend:
    enabled: true
    port: 8000
    cpu: 0.5
    memory: 1.0

  frontend:
    enabled: false

  database:
    enabled: false

environment: "dev"
EOF
```

### 4. Add Your Code
```bash
# Copy your application code
cp -r ~/my-app/* apps/YOUR_TEAM/YOUR_APP/backend/

# Ensure you have a Dockerfile
# Must expose the port from app-config.yml
# Must run on 0.0.0.0 (not localhost)
```

**Example Dockerfile (Python):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

### 5. Register App
```bash
cat >> apps/_registry.yml <<EOF

  - name: your-app
    team: your-team
    path: apps/your-team/your-app
    status: active
    created: "$(date +%Y-%m-%d)"
    environment: dev
    description: "Brief description"
EOF
```

### 6. Test Locally (Recommended)
```bash
# Validate config
python3 platform/validation/validate.py apps/YOUR_TEAM/YOUR_APP/app-config.yml

# Check costs
python3 scripts/estimate-costs.py apps/YOUR_TEAM/YOUR_APP/app-config.yml

# Test Docker build
docker build apps/YOUR_TEAM/YOUR_APP/backend -t test:backend
```

### 7. Create Pull Request
```bash
git checkout -b add-your-app
git add apps/
git commit -m "Add your-app

Brief description of what it does.
Estimated cost: ~£XX/month"
git push origin add-your-app
gh pr create --title "Add your-app" --body "Description"
```

### 8. Review Automated Checks

The platform will comment on your PR with:

- **📋 Changes Detected** - What changed, what will happen
- **✅ Validation Results** - Config is valid (or errors with fixes)
- **💰 Cost Estimation** - Monthly cost breakdown
- **🐳 Dockerfile Checks** - Security and best practices
- **📊 Summary** - Overall status

**If checks fail:** Read the error messages. They include:
- What's wrong
- Why it matters
- How to fix it

Fix issues, push again, and checks re-run automatically.

### 9. Merge to Deploy
```bash
gh pr merge --squash --delete-branch
```

**Deployment takes 7-10 minutes:**
- Phase 1: Create Azure Container Registry (~2 min)
- Phase 2: Build Docker images (~3-5 min)
- Phase 3: Deploy containers (~2-3 min)

### 10. Access Your App
```bash
# Watch deployment
gh run watch

# Or view in browser
gh run view --web
```

**URLs shown in workflow summary:**
- Backend: `https://your-app-backend.uksouth.azurecontainer.io`
- Frontend: `https://your-app-frontend.uksouth.azurecontainer.io`

Done! Your app is live on Azure.

## Configuration Reference

### Required Fields
```yaml
app:
  name: "app-name"        # 3-15 chars, lowercase, unique
  team: "team-name"       # Your team name

components:
  backend:
    enabled: true/false   # Deploy backend?
  frontend:
    enabled: true/false   # Deploy frontend?
  database:
    enabled: true/false   # Deploy database?

environment: "dev"        # dev, staging, or prod
```

### Optional Fields
```yaml
app:
  region: "uksouth"              # Default: uksouth
  description: "..."             # Recommended

components:
  backend:
    port: 8000                   # Default: 8000
    cpu: 0.5-4.0                 # Default: 1.0 cores
    memory: 0.5-8.0              # Default: 1.5 GB

  database:
    type: postgresql/mysql       # Default: postgresql
    tier: Basic/GeneralPurpose   # Default: Basic
    storage_mb: 5120-1048576     # Default: 32768 (32GB)
```

## Cost Guide

### Typical Monthly Costs (Azure UK South)

| Configuration | Cost |
|--------------|------|
| Backend only (0.5 core, 1GB) | ~£15 |
| Backend only (1 core, 1.5GB) | ~£30 |
| Backend + Frontend | ~£45 |
| + PostgreSQL Basic | +£25 |
| + PostgreSQL GeneralPurpose | +£55 |

**Cost Breakdown Example:**
```
Backend: 0.5 CPU, 1.0GB RAM
├─ CPU:    £7.50/month (0.5 × £15.00/core)
├─ Memory: £7.50/month (1.0GB × £7.50/GB)
└─ Total:  £15.00/month

💡 Tip: Reduce to 0.25 cores and 0.5GB to save £7.50/month
```

### Reduce Costs
- Disable database for dev/test
- Use lower CPU/memory (0.5 core, 1GB)
- Destroy resources when not in use

## Common Issues

### "App name already exists"
Another app uses that name. Choose a different name.

### "Backend enabled but Dockerfile not found"
Missing `apps/YOUR_TEAM/YOUR_APP/backend/Dockerfile`. Create it.

### "Validation failed"
Read the error message. It tells you:
- What's wrong
- Why it matters
- How to fix

### "Deployment failed"
Check workflow logs: `gh run view --log`

Most common causes:
- Resource name conflicts
- Azure quota limits
- Missing configuration

## Best Practices

1. **Start small** - Deploy with minimal resources (0.5 core, 1GB), scale up if needed
2. **Test locally** - Run validation and Docker build before creating PR
3. **Read errors** - Error messages include how to fix issues
4. **Check costs** - Review estimates before merging
5. **Descriptive names** - Use clear app names like `customer-api`, not `app1`

## Architecture Deep Dive

See [ARCHITECTURE.md](ARCHITECTURE.md) for:
- Detailed system architecture with diagrams
- Component explanations
- Data flow diagrams
- Design decisions (ADRs)
- Security model
- State management
- Technology stack

## Getting Help

**Validation errors?** Read the error message - it includes how to fix
**Cost questions?** Check the estimation output in PR
**Deployment issues?** Check workflow logs: `gh run view --log`
**General questions?** Check [apps/README.md](apps/README.md) or contact @platform-team

## What Makes This Different?

### Traditional Azure Deployment
```
1. Learn Azure Portal
2. Learn Terraform
3. Create resources manually
4. Configure credentials per repo
5. No validation before deployment
6. No cost visibility
7. Inconsistent infrastructure
```

### This Platform
```
1. Write 20 lines of YAML
2. Create PR
3. Review automated feedback
4. Merge
5. App deployed automatically
```

**Key benefits:**
- No Azure knowledge required
- Validation catches errors early
- Cost transparency before deployment
- Consistent, secure infrastructure
- Self-service deployment

## Example: Complete Walkthrough

Deploy a Flask API in 5 minutes:

```bash
# 1. Create structure
mkdir -p apps/demo/hello-api/backend

# 2. Add app code
cat > apps/demo/hello-api/backend/app.py <<'EOF'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({"message": "Hello from Azure!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
EOF

cat > apps/demo/hello-api/backend/requirements.txt <<EOF
flask==3.0.0
gunicorn==21.2.0
EOF

cat > apps/demo/hello-api/backend/Dockerfile <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
EOF

# 3. Add config
cat > apps/demo/hello-api/app-config.yml <<EOF
app:
  name: "hello-api"
  team: "demo"
  region: "uksouth"
components:
  backend:
    enabled: true
    port: 8000
    cpu: 0.5
    memory: 1.0
  frontend:
    enabled: false
  database:
    enabled: false
environment: "dev"
EOF

# 4. Register
cat >> apps/_registry.yml <<EOF

  - name: hello-api
    team: demo
    path: apps/demo/hello-api
    status: active
    created: "$(date +%Y-%m-%d)"
    environment: dev
    description: "Hello world API"
EOF

# 5. Test
python3 platform/validation/validate.py apps/demo/hello-api/app-config.yml
python3 scripts/estimate-costs.py apps/demo/hello-api/app-config.yml

# 6. Deploy
git checkout -b add-hello-api
git add apps/
git commit -m "Add hello-api"
git push origin add-hello-api
gh pr create --title "Add hello-api" --body "Demo API"
# Review checks, merge PR
# Wait ~7 minutes
# Access at: https://hello-api-backend.uksouth.azurecontainer.io
```

---

**Ready to deploy?** Follow the [Quick Start](#quick-start-deploy-an-app-in-10-minutes) above!
