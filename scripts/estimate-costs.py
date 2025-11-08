#!/usr/bin/env python3
"""
Azure Cost Estimation Script

Estimates monthly Azure costs for an app deployment based on app-config.yml.
Provides detailed breakdown with explanations and optimization suggestions.

Usage:
    python estimate-costs.py <path-to-app-config.yml>

Output:
    Markdown-formatted cost breakdown
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List

# Azure UK South pricing (as of January 2025)
# Prices in GBP per month unless otherwise noted
PRICING = {
    'container_instance': {
        'cpu_per_core_per_second': 0.0000125,  # £/second
        'memory_per_gb_per_second': 0.0000014,  # £/second
    },
    'container_registry': {
        'basic': 4.22,  # £/month
        'standard': 16.88,
        'premium': 42.20,
    },
    'postgresql': {
        'basic': {
            'base': 21.10,  # £/month for smallest instance
            'storage_per_gb': 0.084,  # £/GB/month
        },
        'general_purpose': {
            'base': 52.75,
            'storage_per_gb': 0.084,
        }
    },
    'mysql': {
        'basic': {
            'base': 21.10,
            'storage_per_gb': 0.084,
        }
    }
}

SECONDS_PER_MONTH = 30 * 24 * 60 * 60  # Approximately 2,592,000 seconds


class CostEstimator:
    """Estimates Azure costs with explanations"""

    def __init__(self, config_path: Path):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.costs = {}
        self.explanations = []

    def estimate(self) -> Dict:
        """Calculate all costs and return breakdown"""

        # Container Registry (shared resource)
        self._estimate_acr()

        # Backend container
        if self.config.get('components', {}).get('backend', {}).get('enabled'):
            self._estimate_backend()

        # Frontend container
        if self.config.get('components', {}).get('frontend', {}).get('enabled'):
            self._estimate_frontend()

        # Database
        if self.config.get('components', {}).get('database', {}).get('enabled'):
            self._estimate_database()

        return {
            'total': sum(self.costs.values()),
            'breakdown': self.costs,
            'explanations': self.explanations
        }

    def _estimate_acr(self):
        """Estimate Container Registry costs"""
        cost = PRICING['container_registry']['basic']
        self.costs['acr'] = cost

        self.explanations.append({
            'resource': 'Azure Container Registry',
            'cost': cost,
            'config': 'Basic tier',
            'why': (
                'Stores your Docker images. Basic tier is sufficient for most apps. '
                'This is shared across all apps in the platform, so the cost is split.'
            ),
            'savings_tip': (
                'Shared across all platform apps, so actual cost per app is lower. '
                f'With 10 apps, your share would be £{cost / 10:.2f}/month'
            )
        })

    def _estimate_backend(self):
        """Estimate backend container costs"""
        backend = self.config['components']['backend']
        cpu = backend.get('cpu', 1.0)
        memory = backend.get('memory', 1.5)
        port = backend.get('port', 8000)

        # Calculate monthly cost
        cpu_cost = cpu * PRICING['container_instance']['cpu_per_core_per_second'] * SECONDS_PER_MONTH
        memory_cost = memory * PRICING['container_instance']['memory_per_gb_per_second'] * SECONDS_PER_MONTH
        total_cost = cpu_cost + memory_cost

        self.costs['backend'] = total_cost

        # Calculate what it would cost with half resources
        half_cpu_cost = (cpu / 2) * PRICING['container_instance']['cpu_per_core_per_second'] * SECONDS_PER_MONTH
        half_memory_cost = (memory / 2) * PRICING['container_instance']['memory_per_gb_per_second'] * SECONDS_PER_MONTH
        half_total = half_cpu_cost + half_memory_cost

        self.explanations.append({
            'resource': 'Backend Container Instance',
            'cost': total_cost,
            'config': f'{cpu} CPU cores, {memory}GB RAM, port {port}',
            'breakdown': f'CPU: £{cpu_cost:.2f}/month + Memory: £{memory_cost:.2f}/month',
            'why': (
                'Always-on container running your backend API. '
                'Charged per second of runtime with these resource allocations.'
            ),
            'savings_tip': (
                f'Reduce to {cpu / 2} cores and {memory / 2}GB RAM to save £{total_cost - half_total:.2f}/month '
                f'(new cost: £{half_total:.2f}/month). Test if your app still performs well.'
            )
        })

    def _estimate_frontend(self):
        """Estimate frontend container costs"""
        frontend = self.config['components']['frontend']
        cpu = frontend.get('cpu', 0.5)
        memory = frontend.get('memory', 1.0)

        cpu_cost = cpu * PRICING['container_instance']['cpu_per_core_per_second'] * SECONDS_PER_MONTH
        memory_cost = memory * PRICING['container_instance']['memory_per_gb_per_second'] * SECONDS_PER_MONTH
        total_cost = cpu_cost + memory_cost

        self.costs['frontend'] = total_cost

        self.explanations.append({
            'resource': 'Frontend Container Instance',
            'cost': total_cost,
            'config': f'{cpu} CPU cores, {memory}GB RAM',
            'breakdown': f'CPU: £{cpu_cost:.2f}/month + Memory: £{memory_cost:.2f}/month',
            'why': 'Serves your frontend application (web UI)',
            'savings_tip': (
                'Frontend typically needs less resources than backend. '
                f'Current allocation seems reasonable for a web app.'
            )
        })

    def _estimate_database(self):
        """Estimate database costs"""
        database = self.config['components']['database']
        db_type = database.get('type', 'postgresql')
        tier = database.get('tier', 'Basic').lower().replace(' ', '_')
        storage_mb = database.get('storage_mb', 32768)
        storage_gb = storage_mb / 1024

        if db_type == 'postgresql':
            pricing = PRICING['postgresql'].get(tier, PRICING['postgresql']['basic'])
        else:
            pricing = PRICING['mysql'].get(tier, PRICING['mysql']['basic'])

        base_cost = pricing['base']
        storage_cost = storage_gb * pricing['storage_per_gb']
        total_cost = base_cost + storage_cost

        self.costs['database'] = total_cost

        self.explanations.append({
            'resource': f'{db_type.title()} Database',
            'cost': total_cost,
            'config': f'{tier.replace("_", " ").title()} tier, {storage_gb:.0f}GB storage',
            'breakdown': f'Instance: £{base_cost:.2f}/month + Storage: £{storage_cost:.2f}/month',
            'why': (
                'Managed database with automated backups, patching, and high availability. '
                'Saves you from managing database infrastructure yourself.'
            ),
            'savings_tip': (
                'For dev/test environments, consider disabling the database and using SQLite or a shared dev database. '
                f'This would save £{total_cost:.2f}/month.'
            )
        })

    def generate_markdown_report(self) -> str:
        """Generate markdown-formatted cost report"""
        result = self.estimate()

        lines = []
        lines.append(f"### 💰 Monthly Cost Estimate: £{result['total']:.2f}")
        lines.append("")
        lines.append("| Resource | Cost | Configuration | Why You Need This |")
        lines.append("|----------|------|---------------|-------------------|")

        for exp in result['explanations']:
            cost_str = f"£{exp['cost']:.2f}"
            config_str = exp.get('config', 'N/A')
            why_str = exp['why']
            lines.append(f"| {exp['resource']} | {cost_str} | {config_str} | {why_str} |")

        lines.append("")
        lines.append("#### 💡 Cost Breakdown Details")
        lines.append("")

        for exp in result['explanations']:
            if 'breakdown' in exp:
                lines.append(f"**{exp['resource']}:**")
                lines.append(f"- {exp['breakdown']}")
                lines.append("")

        lines.append("#### 💸 Cost Saving Tips")
        lines.append("")

        for exp in result['explanations']:
            if 'savings_tip' in exp:
                lines.append(f"- **{exp['resource']}:** {exp['savings_tip']}")

        lines.append("")
        lines.append(f"**Total estimated monthly cost: £{result['total']:.2f}**")
        lines.append("")
        lines.append("#### 📊 Annual Projection")
        annual = result['total'] * 12
        lines.append(f"- Annual cost: £{annual:.2f}")
        lines.append(f"- Using Azure free credits (£200): Covers ~{200 / result['total']:.1f} months")
        lines.append("")
        lines.append("#### ℹ️ Notes")
        lines.append("")
        lines.append("- Prices based on Azure UK South region, January 2025")
        lines.append("- Actual costs may vary based on:")
        lines.append("  - Data transfer (outbound traffic)")
        lines.append("  - Actual container uptime")
        lines.append("  - Database query performance")
        lines.append("  - Azure pricing changes")
        lines.append("- Set up cost alerts in Azure Portal to monitor actual spend")
        lines.append("- Consider destroying dev/test environments when not in use")

        return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python estimate-costs.py <path-to-app-config.yml>")
        sys.exit(1)

    config_path = Path(sys.argv[1])

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    estimator = CostEstimator(config_path)
    report = estimator.generate_markdown_report()
    print(report)


if __name__ == '__main__':
    main()
