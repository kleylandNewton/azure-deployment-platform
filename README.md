# Azure Deployment Platform

**Centralized platform for deploying and managing Azure applications**

## Overview

This platform enables teams to deploy containerized applications to Azure with:
- ✅ Centralized credential management
- ✅ Automated validation and standards enforcement
- ✅ Cost estimation and tracking
- ✅ Detailed deployment explanations
- ✅ Self-service via Pull Requests

## Quick Start

### For Users: Deploy Your App

1. **Create a new app folder**
   ```bash
   mkdir -p apps/your-team/your-app
   ```

2. **Add your configuration**
   ```bash
   cp apps/_template/app-config.yml apps/your-team/your-app/
   # Edit the config file
   ```

3. **Add your application code**
   ```bash
   cp -r ~/your-app-code/* apps/your-team/your-app/
   ```

4. **Create Pull Request**
   - Automated validation will run
   - Cost estimates will be posted
   - Platform team will review
   - On merge, your app deploys automatically!

### For Platform Team: Initial Setup

See [Setup Guide](platform/docs/setup-guide.md) for detailed instructions.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Users create PR → Validation runs → Costs estimated   │
│  Platform team reviews → PR merges → Auto-deployment   │
└─────────────────────────────────────────────────────────┘
```

### What Gets Created Per App

Each app deployment creates:
- Azure Container Registry (shared)
- Resource Group (per app)
- Container Instances (backend/frontend)
- PostgreSQL Database (optional)
- Application Insights (monitoring)

All with unique, standardized names.

## Repository Structure

```
azure-deployment-platform/
├── apps/                    # User applications
│   ├── _registry.yml       # Master list of all apps
│   ├── team-a/
│   │   └── app-1/
│   │       ├── app-config.yml
│   │       ├── backend/
│   │       └── frontend/
│   └── team-b/
│       └── app-2/
│
├── platform/               # Platform infrastructure
│   ├── terraform/         # Shared Terraform modules
│   ├── validation/        # Validation rules
│   └── docs/             # Documentation
│
└── .github/workflows/     # CI/CD pipelines
```

## Key Features

### 1. Explainable Deployments

Every step is explained:
- **What** is being deployed
- **Why** each resource is needed
- **How much** it will cost
- **What changed** from last deployment

### 2. Automated Validation

Before deployment, we check:
- ✅ Configuration schema
- ✅ Dockerfile best practices
- ✅ Security vulnerabilities
- ✅ Cost estimates
- ✅ Naming conventions

### 3. Cost Transparency

Automated cost estimation shows:
- Per-resource costs
- Monthly totals
- Optimization suggestions
- Comparison with previous deployments

### 4. Access Control

Using GitHub CODEOWNERS:
- Teams can only modify their apps
- Platform team controls infrastructure
- All changes require approval

## Documentation

- [Onboarding Guide](platform/docs/onboarding.md) - How to add your app
- [Architecture Decisions](platform/docs/decision-log.md) - Why we made these choices
- [Troubleshooting](platform/docs/troubleshooting.md) - Common issues
- [Cost Management](platform/docs/cost-management.md) - Controlling costs

## Support

- **Issues:** Create GitHub issue
- **Questions:** Check documentation
- **Security:** Contact platform team

## License

MIT
