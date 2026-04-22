"""Analyzer Agent - Code review and vulnerability analysis."""

import logging
import re
from typing import Optional, Dict, Any, List, Set

from agents.base_agent import BaseAgent

logger = logging.getLogger("phantom.analyzeragent")


class AnalyzerAgent(BaseAgent):
    """Agent for code analysis and vulnerability identification."""

    VULN_PATTERNS = {
        "SQL Injection": [
            r'execute\s*\([' ,
            r'query\s*\(',
            r'SELECT.*FROM',
            r'INSERT.*INTO',
            r'UPDATE.*SET',
            r'\.format\(',
            r'%s.*%',
        ],
        "XSS": [
            r'innerHTML',
            r'outerHTML',
            r'document\.write',
            r'\.html\(',
            r'dangerouslySetInnerHTML',
        ],
        "Command Injection": [
            r'exec\s*\(',
            r'system\s*\(',
            r'popen\s*\(',
            r'shell_exec',
            r'Subprocess',
            r'os\.system',
        ],
        "Path Traversal": [
            r'\.\./',
            r'\.\.\\\\',
            r'open\s*\(\s*request\.',
            r'Path\s*\(\s*user',
        ],
        "Weak Crypto": [
            r'md5',
            r'sha1',
            r'DES',
            r'RC4',
        ],
        "Hardcoded Secret": [
            r'password\s*=',
            r'api[_-]?key\s*=',
            r'secret\s*=',
            r'token\s*=',
        ],
        "Insecure Deserialization": [
            r'pickle\.load',
            r'yaml\.load',
            r'unserialize',
        ],
        "SSRF": [
            r'requests\.get\s*\(\s*url',
            r'urllib\.urlopen',
            r'fetch\s*\(\s*url',
        ],
    }

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run analysis task."""
        if context and "code" in context:
            return await self.analyze_code(context["code"])

        return "No code provided for analysis."

    async def analyze_code(
        self,
        code: str,
        language: Optional[str] = None
    ) -> str:
        """Analyze code for vulnerabilities."""
        vulnerabilities = self._find_vulnerabilities(code)

        if not vulnerabilities:
            return "## Analysis Result\n\nNo obvious vulnerabilities detected."

        output = "## Vulnerability Analysis\n\n"
        output += f"**Findings: {len(vulnerabilities)}**\n\n"

        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for vuln in vulnerabilities:
            severity_counts[vuln["severity"]] += 1

        output += "| Severity | Count |\n"
        output += "|----------|-------|\n"
        for severity, count in severity_counts.items():
            if count > 0:
                output += f"| {severity} | {count} |\n"

        output += "\n### Details\n\n"

        for vuln in vulnerabilities[:20]:
            output += f"#### {vuln['type']} - {vuln['severity']}\n"
            output += f"**Line:** {vuln['line']}\n"
            output += f"**Code:** ```\n{vuln['code']}\n```\n"
            output += f"**Recommendation:** {vuln['recommendation']}\n\n"

        return output

    def _find_vulnerabilities(self, code: str) -> List[Dict[str, Any]]:
        """Find vulnerabilities in code."""
        vulnerabilities = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            for vuln_type, patterns in self.VULN_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        vuln = self._create_vulnerability(
                            vuln_type, line, i
                        )
                        if vuln:
                            vulnerabilities.append(vuln)
                        break

        return vulnerabilities

    def _create_vulnerability(
        self,
        vuln_type: str,
        code: str,
        line: int
    ) -> Optional[Dict[str, Any]]:
        """Create vulnerability report."""
        severity_map = {
            "SQL Injection": "HIGH",
            "XSS": "HIGH",
            "Command Injection": "CRITICAL",
            "Path Traversal": "MEDIUM",
            "Weak Crypto": "MEDIUM",
            "Hardcoded Secret": "HIGH",
            "Insecure Deserialization": "CRITICAL",
            "SSRF": "HIGH",
        }

        recommendation_map = {
            "SQL Injection": "Use parameterized queries or an ORM.",
            "XSS": "Use textContent() or sanitize input.",
            "Command Injection": "Avoid shell commands. Use APIs directly.",
            "Path Traversal": "Validate and sanitize file paths.",
            "Weak Crypto": "Use AES-256 or ChaCha20.",
            "Hardcoded Secret": "Use environment variables or secrets manager.",
            "Insecure Deserialization": "Use secure serialization formats.",
            "SSRF": "Validate URLs and restrict access.",
        }

        return {
            "type": vuln_type,
            "severity": severity_map.get(vuln_type, "MEDIUM"),
            "line": line,
            "code": code.strip()[:100],
            "recommendation": recommendation_map.get(
                vuln_type, "Review this code."
            ),
        }

    async def think(self, query: str, mode: str = "paranoid") -> Any:
        """Use paranoid thinking for security analysis."""
        return await super().think(query, mode=mode)

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return [
            "code_analysis",
            "vulnerability_scan",
            "secure_coding",
        ]