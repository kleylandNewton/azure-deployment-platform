# App Deployment Request

## App Information

**App Name:**
**Team:**
**Type:** [ ] New App [ ] Update Existing [ ] Configuration Change

## Description

<!-- Describe what this deployment does -->

## Configuration Changes

<!-- Summarize changes to app-config.yml if applicable -->

## Estimated Monthly Cost

<!-- Will be automatically calculated and posted as comment -->

## Pre-Deployment Checklist

### Required (Automated Checks)
- [ ] app-config.yml follows schema
- [ ] Dockerfiles pass lint checks
- [ ] No critical security vulnerabilities
- [ ] App name is unique
- [ ] Team is registered

### Manual Review
- [ ] I have tested the Docker build locally
- [ ] I have reviewed the estimated costs
- [ ] I have updated apps/_registry.yml (for new apps)
- [ ] I understand what resources will be created

## Questions for Platform Team

<!-- Any specific questions or concerns? -->

---

**Note:** Automated validation will run when you create this PR. Check the comments below for:
- ✅ Validation results
- 💰 Cost estimates
- 🐳 Dockerfile recommendations
- 🔒 Security scan results

Platform team will review after all checks pass.
