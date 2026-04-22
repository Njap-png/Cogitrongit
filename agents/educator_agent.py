"""Educator Agent - Adaptive teaching and CTF mode."""

import logging
import json
from typing import Optional, Dict, Any, List

from agents.base_agent import BaseAgent

logger = logging.getLogger("phantom.educatoragent")


class EducatorAgent(BaseAgent):
    """Agent for adaptive teaching and CTF challenges."""

    SKILL_LEVELS = ["beginner", "intermediate", "advanced", "expert"]

    TOPICS = [
        "networking",
        "web_security",
        "cryptography",
        "reverse_engineering",
        "binary_exploitation",
        "forensics",
        "osint",
        "privilege_escalation",
    ]

    async def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run educational task."""
        parts = task.split(None, 1)
        command = parts[0].lower()
        data = parts[1] if len(parts) > 1 else ""

        if command == "teach":
            return await self.teach_topic(data, context)

        if command == "ctf":
            return await self.ctf_challenge(data, context)

        if command == "explain":
            return await self.explain_concept(data)

        if command == "quiz":
            return await self.quiz(data)

        if command == "skill":
            return self.set_skill_level(data)

        return await self.teach_topic(task, context)

    async def teach_topic(
        self,
        topic: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Teach a topic at appropriate skill level."""
        skill_level = context.get("skill_level", "intermediate") if context else "intermediate"

        prompt = f"""Create a comprehensive lesson on {topic} for a {skill_level} level student.
Include:
- Overview and key concepts
- Real-world examples
- Hands-on exercises
- Common pitfalls
- Defensive countermeasures

Vary complexity based on skill level:
- Beginner: Focus on fundamentals
- Intermediate: Include practical examples
- Advanced: Deep technical details
- Expert: Cutting-edge techniques and research

Format output with clear sections and code examples where applicable."""

        thinking_result = await self.think(prompt, mode="deep")
        return thinking_result.final_answer

    async def ctf_challenge(
        self,
        category: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a CTF challenge."""
        skill_level = context.get("skill_level", "intermediate") if context else "intermediate"

        prompt = f"""Create a CTF challenge for {category} at {skill_level} difficulty.
Include:
- Challenge title and description
- Category and points
- Files or access information
- Hints (progressive)
- Flag format (e.g., PHANTOM{{...}})

The challenge should be:
- Solvable with appropriate tools
- Educational
- Realistic scenario

Output in this format:
## [Title]
**Category:** ...
**Points:** ...
**Description:** ...

[Challenge details]

### Hints
1. ...
2. ...
3. ...

### Flag Format
PHANTOM{{...}}
"""

        thinking_result = await self.think(prompt, mode="deep")
        return thinking_result.final_answer

    async def explain_concept(self, concept: str) -> str:
        """Explain a specific concept."""
        prompt = f"""Explain the following concept in cybersecurity:
{concept}

Include:
- What it is
- How it works
- Real-world applications
- Attack and defense perspectives
- Code examples if applicable

Keep it concise but thorough."""

        thinking_result = await self.think(prompt, mode="fast")
        return thinking_result.final_answer

    async def quiz(self, topic: str) -> str:
        """Generate a quiz on a topic."""
        prompt = f"""Generate a 5-question quiz on {topic}.
Include:
- Multiple choice (4 options)
- True/False
- Short answer questions

Cover different aspects of the topic.
Include an answer key at the end.

Format:
## Quiz: {topic}

### Question 1
[Question]
- A) [Option]
- B) [Option]
- C) [Option]
- D) [Option]

Answer: [Letter]

[Continue for all questions]

## Answer Key
1. [Answer]
2. [Answer]
...
"""

        thinking_result = await self.think(prompt, mode="fast")
        return thinking_result.final_answer

    def set_skill_level(self, level: str) -> str:
        """Set skill level."""
        level = level.lower()

        if level not in self.SKILL_LEVELS:
            return f"Invalid level. Choose from: {', '.join(self.SKILL_LEVELS)}"

        return f"Skill level set to: {level}"

    def list_topics(self) -> str:
        """List available topics."""
        output = "## Topics\n\n"

        for topic in self.TOPICS:
            output += f"- **{topic}**\n"

        return output

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return [
            "adaptive_teaching",
            "ctf_challenges",
            "concept_explanation",
            "quiz_generation",
        ]