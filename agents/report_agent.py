"""Report Agent - Vulnerability reports and bug bounty."""

import logging
from typing import Optional, Dict, Any, List

from agents.base_agent import BaseAgent
from datetime import datetime

logger = logging.getLogger("phantom.reportagent")


class ReportAgent(BaseAgent):
    """Agent for vulnerability reports and documentation."""

    TEMPLATES = {
        "bugbounty": """# Bug Bounty Report

## Vulnerability Details
- **Title:**
- **Severity:** Critical/High/Medium/Low
- **CVSS Score:**
- **Affected Component:**

## Description
[Detailed description of the vulnerability]

## Steps to Reproduce
1.
2.
3.

## Impact
[Security impact on users/systems]

## Remediation
[Recommended fix]

## Timeline
- Discovered:
- Reported:
- Acknowledged:
- Fixed:
""",
        "vuln_assessment": """# Vulnerability Assessment

## Executive Summary
[High-level overview]

## Scope
[Systems/components assessed]

## Methodology
- Reconnaissance
- Scanning
- Enumeration
- Analysis

## Findings

### Critical
[Critical vulnerabilities]

### High
[High severity issues]

### Medium
[Medium severity issues]

### Low
[Low severity issues]

## Recommendations
[Prioritized remediation steps]

## Conclusion
[Overall security posture]
""",
        "pentest": """# Penetration Test Report

## Project Information
- **Date:**
- **Tester:**
- **Scope:**

## Methodology
[Testing methodology used]

## Findings Summary
| Severity | Count |
|----------|-------|
| Critical | |
| High | |
| Medium | |
| Low | |

## Detailed Findings
[Detailed vulnerability descriptions]

## Remediation Matrix
| Finding | Severity | Remediation | Priority |
|---------|----------|------------|----------|

## Conclusion
[Summary and next steps]
""",
    }

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run report generation task."""
        task_lower = task.lower()

        if task_lower.startswith("template "):
            template_name = task.split()[1].lower()
            return self.get_template(template_name)

        if task_lower.startswith("generate "):
            parts = task.split(None, 2)
            if len(parts) < 3:
                return "Usage: generate <type> <data>"
            return await self.generate_report(parts[1], parts[2], context)

        if task_lower.startswith("cve "):
            cve_id = task.split()[1]
            return await self.cve_report(cve_id)

        return self.list_templates()

    def get_template(self, template_name: str) -> str:
        """Get report template."""
        if template_name in self.TEMPLATES:
            return self.TEMPLATES[template_name]

        return f"Unknown template: {template_name}"

    def list_templates(self) -> str:
        """List available templates."""
        output = "## Available Templates\n\n"

        for name in self.TEMPLATES:
            output += f"- **{name}**\n"

        output += "\nUsage: `template <name>` to get the template."
        return output

    async def generate_report(
        self,
        report_type: str,
        data: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a report from data."""
        prompt = f"""Generate a comprehensive {report_type} report based on the following data.
Follow professional security reporting standards.

Data: {data}

Output the complete report in Markdown format."""

        thinking_result = await self.think(prompt, mode="deep")
        return thinking_result.final_answer

    async def cve_report(self, cve_id: str) -> str:
        """Get CVE report."""
        from tools.web_search import WebSearch

        searcher = WebSearch(self.config)
        cve = searcher.search_cve(cve_id)

        if not cve:
            return f"CVE {cve_id} not found."

        output = f"## {cve.cve_id}\n\n"
        output += f"**Severity:** {cve.severity}\n"
        if cve.cvss_score:
            output += f"**CVSS Score:** {cve.cvss_score}\n"
        output += f"**Published:** {cve.published}\n\n"

        output += "### Description\n\n"
        output += f"{cve.description}\n\n"

        if cve.affected:
            output += "### Affected Products\n\n"
            for product in cve.affected[:10]:
                output += f"- {product}\n"

        if cve.references:
            output += "\n### References\n\n"
            for ref in cve.references[:5]:
                output += f"- {ref}\n"

        return output

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return [
            "template_generation",
            "report_creation",
            "cve_research",
        ]