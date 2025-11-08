#!/usr/bin/env python3
"""
App Configuration Validator

This script validates app-config.yml files against the platform schema.
It provides detailed, actionable error messages to help developers fix issues quickly.

Usage:
    python validate.py <path-to-app-config.yml>

Returns:
    Exit code 0 if valid, 1 if invalid
    Prints JSON with validation results
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("Error: jsonschema not installed. Run: pip install jsonschema pyyaml")
    sys.exit(1)


class AppConfigValidator:
    """Validates app configuration with helpful error messages"""

    def __init__(self, schema_path: Path = None):
        if schema_path is None:
            schema_path = Path(__file__).parent / "schemas/app-config.schema.json"

        with open(schema_path) as f:
            self.schema = json.load(f)

    def validate(self, config_path: Path) -> Tuple[bool, List[Dict]]:
        """
        Validate app-config.yml file

        Returns:
            (is_valid, errors): Tuple of boolean and list of error dicts
        """
        errors = []

        # Step 1: Parse YAML
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            errors.append({
                "error": f"File not found: {config_path}",
                "why_this_matters": "We need an app-config.yml file to know how to deploy your app",
                "fix": f"Create {config_path} using the template from apps/_template/",
                "severity": "critical",
                "docs_link": "platform/docs/onboarding.md#step-2-create-configuration"
            })
            return False, errors
        except yaml.YAMLError as e:
            errors.append({
                "error": "Failed to parse YAML",
                "details": str(e),
                "why_this_matters": "YAML syntax errors prevent us from reading your configuration",
                "fix": "Check YAML syntax at https://www.yamllint.com/ or use a YAML linter",
                "severity": "critical"
            })
            return False, errors

        # Step 2: Validate against schema
        try:
            jsonschema.validate(config, self.schema)
        except ValidationError as e:
            error_dict = self._explain_validation_error(e, config_path)
            errors.append(error_dict)
            return False, errors

        # Step 3: Custom validations
        custom_errors = self._custom_validations(config, config_path)
        errors.extend(custom_errors)

        return len(errors) == 0, errors

    def _explain_validation_error(self, error: ValidationError, config_path: Path) -> Dict:
        """Convert jsonschema error to helpful explanation"""
        field_path = ".".join(str(p) for p in error.path) if error.path else "root"

        # Get explanation for this field
        explanation = self._get_field_explanation(field_path)
        fix_suggestion = self._get_fix_suggestion(error)

        return {
            "error": error.message,
            "field": field_path,
            "why_this_matters": explanation,
            "fix": fix_suggestion,
            "severity": "error",
            "docs_link": self._get_docs_link(field_path)
        }

    def _get_field_explanation(self, field_path: str) -> str:
        """Explain why each field matters"""
        explanations = {
            "app.name": (
                "App name is used in all Azure resource names (e.g., rg-{name}-dev). "
                "Must be DNS-safe and unique across the platform."
            ),
            "app.team": (
                "Team ownership is used for cost allocation and access control. "
                "Helps us track who owns what and how much each team spends."
            ),
            "app.region": (
                "Azure region determines where your app runs. "
                "Affects latency and compliance requirements."
            ),
            "components.backend.cpu": (
                "CPU allocation affects both performance and monthly costs. "
                "1 core ≈ £20/month. Start low and scale up if needed."
            ),
            "components.backend.memory": (
                "Memory allocation in GB. Affects cost (~£2.5/GB/month) and app performance. "
                "Most apps work fine with 1-2GB."
            ),
            "components.backend.port": (
                "Port your backend listens on. Must match what your Dockerfile EXPOSEs. "
                "Used for health checks and routing."
            ),
            "components.database.enabled": (
                "Deploying a database adds ~£25/month to costs but provides managed, backed-up storage."
            ),
            "environment": (
                "Environment (dev/staging/prod) affects resource naming and potentially sizing. "
                "Helps organize deployments."
            )
        }
        return explanations.get(field_path, "This field is required by the platform configuration")

    def _get_fix_suggestion(self, error: ValidationError) -> str:
        """Provide specific fix suggestions based on error type"""
        if "pattern" in error.schema:
            pattern = error.schema["pattern"]
            if pattern == "^[a-z0-9-]{3,15}$":
                return (
                    f"Use only lowercase letters, numbers, and hyphens. "
                    f"Length must be 3-15 characters. Example: 'my-app' or 'api-service'"
                )

        if error.validator == "required":
            missing = error.message.split("'")[1]
            return f"Add the required field '{missing}' to your configuration"

        if error.validator == "enum":
            allowed = error.schema.get("enum", [])
            return f"Value must be one of: {', '.join(map(str, allowed))}"

        if error.validator == "type":
            expected_type = error.schema.get("type")
            return f"This field must be a {expected_type}"

        if "minimum" in error.schema or "maximum" in error.schema:
            min_val = error.schema.get("minimum", "")
            max_val = error.schema.get("maximum", "")
            return f"Value must be between {min_val} and {max_val}"

        return "Check the schema documentation for correct format"

    def _get_docs_link(self, field_path: str) -> str:
        """Return link to relevant documentation"""
        base_url = "platform/docs/configuration-reference.md"
        return f"{base_url}#{field_path.replace('.', '-')}"

    def _custom_validations(self, config: Dict, config_path: Path) -> List[Dict]:
        """Additional validations beyond schema"""
        errors = []
        app_dir = config_path.parent

        # Check 1: If backend enabled, Dockerfile must exist
        if config.get('components', {}).get('backend', {}).get('enabled'):
            backend_dir = config.get('components', {}).get('backend', {}).get('directory', './backend')
            dockerfile_path = app_dir / backend_dir / 'Dockerfile'

            if not dockerfile_path.exists():
                errors.append({
                    "error": f"Backend enabled but Dockerfile not found at {dockerfile_path}",
                    "why_this_matters": (
                        "We need a Dockerfile to build your backend container image. "
                        "Without it, deployment will fail."
                    ),
                    "fix": (
                        f"Create {dockerfile_path} or set components.backend.enabled to false"
                    ),
                    "severity": "error",
                    "docs_link": "platform/docs/dockerfile-guide.md"
                })

        # Check 2: If frontend enabled, Dockerfile must exist
        if config.get('components', {}).get('frontend', {}).get('enabled'):
            frontend_dir = config.get('components', {}).get('frontend', {}).get('directory', './frontend')
            dockerfile_path = app_dir / frontend_dir / 'Dockerfile'

            if not dockerfile_path.exists():
                errors.append({
                    "error": f"Frontend enabled but Dockerfile not found at {dockerfile_path}",
                    "why_this_matters": "We need a Dockerfile to build your frontend container image",
                    "fix": f"Create {dockerfile_path} or set components.frontend.enabled to false",
                    "severity": "error"
                })

        # Check 3: Warn about high resource allocation (cost implications)
        backend_cpu = config.get('components', {}).get('backend', {}).get('cpu', 0)
        if backend_cpu > 2.0:
            errors.append({
                "error": f"Backend CPU allocation is high: {backend_cpu} cores",
                "why_this_matters": (
                    f"This will cost approximately £{backend_cpu * 20:.2f}/month just for CPU. "
                    "Consider starting with 1-2 cores and scaling up if needed."
                ),
                "fix": "Reduce components.backend.cpu to 1.0 or 2.0 unless you have specific performance requirements",
                "severity": "warning"
            })

        # Check 4: Ensure team is registered
        team = config.get('app', {}).get('team')
        if team:
            registry_path = Path(__file__).parent.parent.parent / "apps/_registry.yml"
            if registry_path.exists():
                with open(registry_path) as f:
                    registry = yaml.safe_load(f)
                    registered_teams = {app.get('team') for app in registry.get('apps', [])}
                    if team not in registered_teams and team != 'pilot':
                        errors.append({
                            "error": f"Team '{team}' not found in registry",
                            "why_this_matters": (
                                "Teams must be registered for cost allocation and access control. "
                                "This prevents typos and ensures proper ownership."
                            ),
                            "fix": (
                                f"1. Add your team to apps/_registry.yml, OR\n"
                                f"2. Use an existing team name: {', '.join(registered_teams)}"
                            ),
                            "severity": "warning"
                        })

        return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate.py <path-to-app-config.yml>")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    validator = AppConfigValidator()
    is_valid, errors = validator.validate(config_path)

    result = {
        "is_valid": is_valid,
        "config_file": str(config_path),
        "errors": errors
    }

    print(json.dumps(result, indent=2))

    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
