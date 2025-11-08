# Architecture Decision Records (ADRs)

This document tracks key architectural decisions made for the Azure Deployment Platform.

Each decision follows this format:
- **Context:** What problem are we solving?
- **Decision:** What did we decide?
- **Rationale:** Why did we make this choice?
- **Consequences:** What are the trade-offs?
- **Alternatives:** What else did we consider?

---

## ADR-001: Use Monorepo for Platform

**Date:** 2025-01-08
**Status:** ✅ Accepted
**Deciders:** Platform Team

### Context

We need to manage multiple teams' applications with centralized control over infrastructure, validation, and deployment processes. We considered three repository structure options:
1. Template pattern (users copy template to their own repos)
2. Multi-repo with registry (users keep code in their repos, register with platform)
3. Monorepo (all code and configs in one repository)

### Decision

Use a monorepo structure where all app configurations and code live in one centralized repository (`azure-deployment-platform`).

### Rationale

**Why this works best:**
- **Centralized validation:** We can enforce standards before deployment (Dockerfiles, configs, security)
- **Single source of truth:** All apps visible in one place - easy to see what's deployed
- **Simplified credentials:** One service principal instead of many per-repo secrets
- **Atomic updates:** Can update platform and apps together without coordination
- **Code review:** All changes go through PR process with platform team visibility
- **Easier onboarding:** New users just create a PR, don't need their own infrastructure

**Why this solves our concerns:**
1. **Code validation:** Can run checks on user code before deployment (Concern #1)
2. **Credential management:** Single set of Azure credentials at org level (Concern #2)

### Consequences

**Positive:**
- ✅ Easier to enforce standards across all apps
- ✅ Simpler credential management (one place)
- ✅ Better visibility into all deployments
- ✅ Can implement platform-wide changes quickly
- ✅ Unified monitoring and cost tracking

**Negative:**
- ❌ Larger repository size as more apps are added
- ❌ Need CODEOWNERS for access control (more setup)
- ❌ Teams see other teams' configs (privacy concerns)
- ❌ Potential merge conflicts if many concurrent PRs

**Mitigations:**
- Use CODEOWNERS to restrict who can modify what
- Branch protection rules to prevent unauthorized changes
- Clear documentation on access control model
- Consider git LFS if repository gets too large
- Migration path to hybrid model later if needed

### Alternatives Considered

**Alternative 1: Pure Template Pattern**
- Users copy template to their own repos
- ❌ Can't validate code before deployment
- ❌ Credential sprawl (Azure secrets in every repo)
- ❌ No central visibility
- ❌ Hard to enforce standards
- ✅ Complete code privacy
- ✅ Simple for users to understand

**Alternative 2: Multi-Repo with Registry**
- Users keep code in their repos, register with platform
- ❌ Complex cross-repo credential management
- ❌ Hard to validate before deployment
- ❌ Requires GitHub App or webhooks
- ✅ Code stays private
- ✅ Teams have full autonomy

**Alternative 3: Hybrid (Git Submodules)**
- Configs in platform repo, code in user repos via submodules
- ❌ Git submodules are complex and error-prone
- ❌ Still need cross-repo access
- ✅ Separation of concerns
- ✅ Code privacy
- **Consideration:** May revisit this if monorepo becomes unwieldy

### References

- Discussion: Initial platform planning session
- Related: ADR-002 (Terraform state management)

---

## ADR-002: Separate Terraform State Per App

**Date:** 2025-01-08
**Status:** ✅ Accepted
**Deciders:** Platform Team

### Context

Terraform needs to store state for infrastructure. With multiple applications, we need to decide how to organize this state. Options:
1. Single state file for all apps
2. Terraform workspaces
3. Separate state file per app

### Decision

Each app gets its own Terraform state file stored in Azure Blob Storage with the pattern: `{team}/{app-name}.tfstate`

### Rationale

**Why separate states:**
- **Blast radius containment:** Error in one app's deployment doesn't affect others
- **Parallel deployments:** Multiple apps can deploy simultaneously without state locking issues
- **Team isolation:** Teams can't accidentally modify other teams' infrastructure
- **Faster operations:** Smaller state files = faster plan/apply
- **Clear ownership:** State file location matches ownership model

**Why not alternatives:**
- Single state file would mean one error could corrupt all deployments
- Terraform workspaces still share the same state file (locking issues)
- Per-app states align with our CODEOWNERS access model

### Consequences

**Positive:**
- ✅ Safer deployments (isolated changes)
- ✅ Better performance (parallel execution)
- ✅ Easier to debug (smaller state to inspect)
- ✅ Can delete app's infrastructure independently

**Negative:**
- ❌ More state files to manage
- ❌ Can't easily query "all deployed apps" from Terraform
- ❌ Slightly more complex CI/CD (dynamic state keys)

**Implementation Details:**
```hcl
# State backend configuration (dynamic per app)
terraform init \
  -backend-config="key=${TEAM}/${APP_NAME}.tfstate" \
  -backend-config="storage_account_name=stplatformtfstate" \
  -backend-config="resource_group_name=rg-platform-terraform-state"
```

### Alternatives Considered

**Alternative 1: Single Shared State**
- All apps in one terraform.tfstate
- ❌ Too dangerous - one corruption affects all apps
- ❌ State locking prevents parallel deployments
- ❌ Very large state file (slow operations)
- ✅ Easy to query all resources

**Alternative 2: Terraform Workspaces**
- Use workspaces to separate apps
- ❌ Still share same state file (locking)
- ❌ Workspace switching is error-prone
- ❌ Limited support in remote backends
- ✅ Built into Terraform

### References

- Terraform Best Practices: https://www.terraform.io/docs/language/state/remote.html
- Azure Backend Documentation: https://www.terraform.io/docs/language/settings/backends/azurerm.html

---

## ADR-003: PR-Based Validation with Required Approvals

**Date:** 2025-01-08
**Status:** ✅ Accepted
**Deciders:** Platform Team

### Context

We need to validate apps before deployment to ensure they meet platform standards. Options:
1. Manual review only
2. Automated checks but optional
3. Automated checks required + manual review
4. Fully automated with no human review

### Decision

All app deployments go through Pull Request workflow with:
1. **Automated validation** (required to pass before merge)
2. **Manual platform team approval** (required)

### Rationale

**Why both automated + manual:**
- Automation catches common errors fast (schema, Dockerfile lint, security)
- Human review catches business logic, architectural issues, costs
- PR comments provide educational feedback to developers
- Creates audit trail of all changes
- Prevents bad deployments before they happen

**What we validate automatically:**
1. ✅ app-config.yml schema compliance
2. ✅ Dockerfile best practices (Hadolint)
3. ✅ Security vulnerabilities (Trivy)
4. ✅ Cost estimation
5. ✅ Naming conventions
6. ✅ Required files exist (Dockerfiles)

### Consequences

**Positive:**
- ✅ Prevents bad deployments
- ✅ Educates developers (feedback in PR)
- ✅ Audit trail for compliance
- ✅ Standardizes all apps
- ✅ Catches security issues early

**Negative:**
- ❌ Slower deployment (wait for approval)
- ❌ Platform team becomes bottleneck
- ❌ More CI/CD complexity

**Mitigations:**
- Platform team commits to review SLA (< 24 hours)
- Clear documentation so PRs pass validation first time
- Automated checks reduce manual review burden
- May add trusted teams who can self-approve later

### Workflow

```
Developer creates PR
  ↓
Automated validation runs
  ├─ Schema check
  ├─ Dockerfile lint
  ├─ Security scan
  └─ Cost estimate
  ↓
Results posted as PR comments
  ↓
If all checks pass → Platform team reviews
  ↓
Platform team approves
  ↓
PR merges → Deployment starts automatically
```

### Alternatives Considered

**Alternative 1: No Validation**
- Just deploy whatever users submit
- ❌ Would lead to deployment failures
- ❌ Security vulnerabilities
- ❌ Cost overruns
- ✅ Fastest to implement

**Alternative 2: Post-Deployment Validation**
- Deploy first, check later
- ❌ Wastes resources on bad deployments
- ❌ Downtime if we need to rollback
- ❌ Harder to fix after deployment

**Alternative 3: Fully Automated (No Human Review)**
- Trust automation completely
- ❌ Can't catch business logic errors
- ❌ No cost oversight
- ❌ No architectural review
- ✅ Fastest deployments
- **Consideration:** May add "trusted teams" tier later

### References

- PR Validation Workflow: `.github/workflows/app-validation.yml`
- Validation Schema: `platform/validation/schemas/app-config.schema.json`

---

## ADR-004: Explainability as First-Class Feature

**Date:** 2025-01-08
**Status:** ✅ Accepted
**Deciders:** Platform Team + User Feedback

### Context

Platform users need to understand:
- Why deployments fail
- What resources are being created
- How much things cost
- What changes will happen

Without clear explanations, users get frustrated and create support tickets.

### Decision

Make explainability a **first-class feature** of the platform:
- Every error message explains what, why, and how to fix
- Every deployment shows detailed progress and reasoning
- Cost estimates are detailed and transparent
- All decisions are documented (ADRs)

### Rationale

**Why this matters:**
- **Education:** Users learn platform standards through feedback
- **Self-service:** Reduce support burden with clear error messages
- **Trust:** Users trust the platform when they understand it
- **Debugging:** Easier to troubleshoot when everything is explained
- **Onboarding:** New users can learn by reading explanations

**Examples of explainability:**
1. Validation errors include "Why this matters" and "How to fix"
2. Deployment workflows log every step with explanations
3. Cost estimates break down per-resource with saving tips
4. ADRs document why we made each architectural choice

### Consequences

**Positive:**
- ✅ Happier users (less frustration)
- ✅ Fewer support tickets
- ✅ Faster onboarding
- ✅ Better debugging
- ✅ Platform improvements through feedback

**Negative:**
- ❌ More code to write (error handling + explanations)
- ❌ More documentation to maintain
- ❌ Longer output logs

**Implementation:**
- All validation errors use structured format with explanation
- All scripts include detailed comments
- All workflows use GitHub Step Summaries
- Cost estimation includes "Why you need this"

### Examples

**Good Error Message:**
```
❌ Error: App name must be 3-15 lowercase characters

Why this matters: App name is used in all Azure resource names.
Must be DNS-safe to work with Azure naming requirements.

How to fix: Change 'MyApp' to 'myapp' or 'my-app'

Docs: platform/docs/configuration-reference.md#app-name
```

**Bad Error Message:**
```
❌ Invalid app name
```

### Alternatives Considered

**Alternative 1: Minimal Error Messages**
- Just show the error, no explanation
- ❌ Users don't learn
- ❌ More support tickets
- ✅ Less code to write

**Alternative 2: Link to Documentation Only**
- Show error + link to docs
- ❌ Context switching (leave PR to read docs)
- ❌ Docs might not cover exact error
- ✅ Less redundant content

**Our Approach: Inline Explanations + Links**
- Show error + explanation + docs link
- ✅ Users get help immediately
- ✅ Can read more if needed
- ✅ Educational

### References

- Validation Script: `platform/validation/validate.py`
- Cost Estimator: `scripts/estimate-costs.py`
- PR Workflow: `.github/workflows/app-validation.yml`

---

## Future ADRs to Consider

These are architectural decisions we haven't made yet but will need to:

- **ADR-005:** Migration to AKS vs staying with ACI
- **ADR-006:** Multi-region deployment strategy
- **ADR-007:** Disaster recovery and backup strategy
- **ADR-008:** Monitoring and alerting architecture
- **ADR-009:** Secrets management (current vs Azure Key Vault)
- **ADR-010:** Cost allocation and chargeback model

---

## Updating This Document

When making a new architectural decision:

1. Create new ADR section with next number
2. Follow the template format
3. Get platform team review
4. Link from related code/docs
5. Update "Future ADRs" if new questions arise

Questions? See `platform/docs/contributing.md`
