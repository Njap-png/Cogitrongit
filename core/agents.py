"""PHANTOM Enhanced Agent System - Autonomous task completion."""

import os
import re
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from core.config import Config
from core.llm import LLMBackend
from core.memory import ConversationMemory
from core.thinking import ThinkingController
from core.soul import Soul
from core.learner import Learner
from core.cli import CLI
from core.updater import SelfUpdater, CodeEditor
from core.sandbox import Sandbox
from core.youtube import VideoLearning, YouTubeExtractor

import logging

logger = logging.getLogger("phantom.agent")


@dataclass
class Task:
    """Task specification."""
    task_id: str
    description: str
    priority: int = 1
    status: str = "pending"
    created_at: str = ""
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    skills_required: List[str] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Agent task response."""
    success: bool
    output: str
    confidence: float
    suggestions: List[str]
    sources: List[str]


class TaskPlanner:
    """Plans and decomposes complex tasks."""

    def __init__(self, llm: LLMBackend):
        """Initialize task planner."""
        self.llm = llm

    async def plan(self, objective: str) -> List[Task]:
        """Break down objective into tasks."""
        prompt = f"""Break down this objective into discrete, executable tasks.
Return JSON array with this structure:
[
  {{
    "task_id": "task_1",
    "description": "Specific action to take",
    "priority": 1-5,
    "skills_required": ["shell", "web_search", "code", "file_edit"]
  }}
]

Objective: {objective}

Rules:
- Each task should be completable in one step
- Higher priority = more important
- Max 10 tasks
- Be specific about what to do"""

        messages = [
            {"role": "system", "content": "You are a task planning assistant. Always return valid JSON."},
            {"role": "user", "content": prompt}
        ]

        result = await self.llm.async_chat(messages)

        try:
            tasks = json.loads(result)
            for i, task in enumerate(tasks):
                task["task_id"] = task.get("task_id", f"task_{i+1}")
                task["created_at"] = datetime.now().isoformat()
            return [Task(**t) for t in tasks]
        except Exception:
            return [
                Task(
                    task_id="task_1",
                    description=objective,
                    created_at=datetime.now().isoformat()
                )
            ]

    def prioritize(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority."""
        return sorted(tasks, key=lambda t: t.priority, reverse=True)


class AutonomousAgent:
    """PHANTOM's autonomous agent with full capabilities."""

    CAPABILITIES = {
        "shell": {
            "description": "Execute shell commands",
            "tools": ["bash", "run", "exec"],
        },
        "web_search": {
            "description": "Search the web",
            "tools": ["search", "crawl", "read"],
        },
        "code": {
            "description": "Write and execute code",
            "tools": ["run", "write", "edit"],
        },
        "file": {
            "description": "File operations",
            "tools": ["read", "write", "edit", "delete"],
        },
        "video": {
            "description": "Video learning",
            "tools": ["yt", "watch", "learn"],
        },
        "knowledge": {
            "description": "Knowledge base",
            "tools": ["kb", "learn", "search"],
        },
        "self_update": {
            "description": "Self-modification",
            "tools": ["update", "patch", "verify"],
        },
    }

    def __init__(
        self,
        config: Optional[Config] = None,
        llm: Optional[LLMBackend] = None,
        memory: Optional[ConversationMemory] = None,
    ):
        """Initialize autonomous agent."""
        self.config = config or Config.get_instance()
        self.llm = llm or LLMBackend(self.config)
        self.memory = memory or ConversationMemory(self.config)

        self.soul = Soul(self.config)
        self.learner = Learner(self.config, self.memory, self.llm)
        self.cli = CLI(self.config)
        self.updater = SelfUpdater(self.config)
        self.code_editor = CodeEditor()
        self.sandbox = Sandbox()
        self.youtube = VideoLearning(self.config)
        self.yt = YouTubeExtractor(self.config)
        self.planner = TaskPlanner(self.llm)

        self._task_queue: List[Task] = []
        self._completed_tasks: Dict[str, Task] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)

    async def execute_task(self, task: Task) -> AgentResponse:
        """Execute a single task."""
        task.status = "running"
        task.created_at = datetime.now().isoformat()

        logger.info(f"Executing: {task.description}")

        try:
            output = await self._execute_by_skills(task)

            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            task.result = output

            self._completed_tasks[task.task_id] = task

            return AgentResponse(
                success=True,
                output=output,
                confidence=0.9,
                suggestions=self._generate_suggestions(output),
                sources=[],
            )

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"Task failed: {e}")

            return AgentResponse(
                success=False,
                output=f"Error: {e}",
                confidence=0.0,
                suggestions=[],
                sources=[],
            )

    async def _execute_by_skills(self, task: Task) -> str:
        """Execute task based on required skills."""
        skills = task.skills_required

        for skill in skills:
            if skill == "shell":
                return await self._execute_shell(task.description)
            elif skill == "web_search":
                return await self._execute_web_search(task.description)
            elif skill == "code":
                return await self._execute_code(task.description)
            elif skill == "file":
                return await self._execute_file(task.description)
            elif skill == "video":
                return await self._execute_video(task.description)
            elif skill == "knowledge":
                return await self._execute_knowledge(task.description)

        return await self._fallback_execute(task.description)

    async def _execute_shell(self, command: str) -> str:
        """Execute shell command."""
        result = self.cli.runner.run(command, timeout=120)
        output = result.output
        if result.error:
            output += f"\nError: {result.error}"
        return output

    async def _execute_web_search(self, query: str) -> str:
        """Execute web search."""
        from tools.web_search import WebSearch
        searcher = WebSearch(self.config)
        results = searcher.search(query, max_results=5)

        if not results:
            return "No results found."

        output = f"Results for: {query}\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r.title}\n   {r.url}\n   {r.snippet[:100]}...\n\n"

        return output

    async def _execute_code(self, description: str) -> str:
        """Execute code."""
        matches = re.findall(r"```\w*\n(.*?)```", description, re.DOTALL)
        if matches:
            code = matches[0]
            language = "python"
            if description.startswith("```bash"):
                language = "bash"
            elif description.startswith("```javascript"):
                language = "javascript"
            elif description.startswith("```js"):
                language = "javascript"

            result = self.sandbox.execute(code, language, timeout=60)
            return result.output if result.success else f"Error: {result.error}"

        result = self.sandbox.execute(description, "python", timeout=60)
        return result.output if result.success else f"Error: {result.error}"

    async def _execute_file(self, description: str) -> str:
        """Execute file operation."""
        if "write" in description.lower() or "create" in description.lower():
            match = re.search(r"(?:to|in)\s+([^\s]+)", description)
            if match:
                file_path = match.group(1)
                content_match = re.search(r"```.*?```", description, re.DOTALL)
                if content_match:
                    content = content_match.group()
                    self.code_editor.write_file(file_path, content)
                    return f"Written to {file_path}"

        if "read" in description.lower():
            match = re.search(r"([^\s]+\.\w+)", description)
            if match:
                file_path = match.group(1)
                content = self.code_editor.read_file(file_path)
                return content[:2000] if content else "File not found"

        return "Could not determine file operation"

    async def _execute_video(self, description: str) -> str:
        """Execute video operation."""
        if "learn" in description.lower():
            url_match = re.search(r"(?:from|on|watching)\s+([^\s]+)", description)
            if url_match:
                url = url_match.group(1)
                video_id = self.yt.get_video_id(url)
                result = self.youtube.extract_and_learn(video_id)
                return f"Learned: {result.get('title', 'Unknown')}\nConcepts: {result.get('concepts', [])}"

        if "search" in description.lower():
            query = description.replace("search", "").strip()
            results = self.youtube.search_youtube(query, max_results=5)
            output = f"YouTube search: {query}\n\n"
            for r in results:
                output += f"- {r.title[:50]} ({r.duration})\n"
            return output

        return "Could not determine video operation"

    async def _execute_knowledge(self, description: str) -> str:
        """Execute knowledge operation."""
        if "learn" in description.lower():
            return "Learning from interaction..."

        if "search" in description.lower():
            query = description.replace("search", "").strip()
            concepts = self.learner.search_knowledge(query, top_k=5)
            output = f"Knowledge search: {query}\n\n"
            for c in concepts:
                output += f"- {c.topic}: {c.key_facts[0] if c.key_facts else 'No details'}\n"
            return output

        return "Could not determine knowledge operation"

    async def _fallback_execute(self, description: str) -> str:
        """Fallback to LLM for complex tasks."""
        prompt = f"""Execute this task and provide the result.
Be specific and thorough.

Task: {description}

If this requires:
- A command, execute it and show output
- Code, run it and show output
- Research, synthesize information
- File editing, describe what was done
- Learning, summarize what was learned"""

        messages = [
            {"role": "system", "content": self.soul.get_persona_prompt()},
            {"role": "user", "content": prompt}
        ]

        return await self.llm.async_chat(messages)

    def _generate_suggestions(self, output: str) -> List[str]:
        """Generate follow-up suggestions."""
        suggestions = []

        if "error" in output.lower():
            suggestions.append("Analyze the error and suggest fixes")

        if "not found" in output.lower():
            suggestions.append("Search alternative sources")

        if len(output) < 100:
            suggestions.append("Get more details")

        return suggestions[:3]

    async def run_objective(
        self,
        objective: str,
        auto_execute: bool = True
    ) -> Dict[str, Any]:
        """Run a complex objective."""
        logger.info(f"Planning objective: {objective}")

        tasks = await self.planner.plan(objective)
        tasks = self.planner.prioritize(tasks)

        results = []
        for task in tasks:
            response = await self.execute_task(task)
            results.append({
                "task": task.description,
                "success": response.success,
                "output": response.output,
            })

            if not response.success:
                break

        all_outputs = "\n".join([r["output"] for r in results])

        return {
            "objective": objective,
            "tasks_planned": len(tasks),
            "tasks_completed": sum(1 for r in results if r["success"]),
            "results": results,
            "combined_output": all_outputs,
        }


class CodeGenerator:
    """Generate and modify code autonomously."""

    LANGUAGES = {
        "python": {
            "boilerplate": "def main():\n    pass\n\nif __name__ == '__main__':\n    main()",
            "style": "pep8",
        },
        "javascript": {
            "boilerplate": "function main() {\n}\n\nmain();",
            "style": "standard",
        },
        "bash": {
            "boilerplate": "#!/bin/bash\nset -e",
            "style": "bash",
        },
    }

    def __init__(self, llm: LLMBackend):
        """Initialize code generator."""
        self.llm = llm

    async def generate(
        self,
        description: str,
        language: str = "python"
    ) -> str:
        """Generate code from description."""
        prompt = f"""Generate complete, working {language} code based on this description.
Do not include placeholders or TODOs. The code should be production-ready.

Description: {description}

Requirements:
- Include proper imports
- Add error handling
- Follow best practices
- Include docstrings/comments
- Return only code in a code block"""

        messages = [
            {"role": "system", "content": f"You are an expert {language} programmer."},
            {"role": "user", "content": prompt}
        ]

        result = await self.llm.async_chat(messages)

        code_match = re.search(r"```(?:\w+)?\n(.*?)```", result, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        return result.strip()

    async def modify(
        self,
        code: str,
        modification: str
    ) -> str:
        """Modify existing code."""
        prompt = f"""Modify this {language} code according to the modification request.
Return only the modified code.

Original Code:
```{code}
```

Modification: {modification}

Return the modified code in a code block."""

        messages = [
            {"role": "system", "content": "You are an expert programmer."},
            {"role": "user", "content": prompt}
        ]

        result = await self.llm.async_chat(messages)

        code_match = re.search(r"```(?:\w+)?\n(.*?)```", result, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        return result.strip()

    async def explain(self, code: str, language: str = "auto") -> str:
        """Explain code."""
        if language == "auto":
            for lang in self.LANGUAGES:
                if f"def {lang}" in code or f"function {lang}" in code:
                    language = lang
                    break

        prompt = f"""Explain this {language} code clearly.
Break down what it does, how it works, and any important details.

Code:
```
{code}
```"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        return await self.llm.async_chat(messages)


class ResearchAgent:
    """Autonomous research agent."""

    def __init__(
        self,
        llm: LLMBackend,
        searcher: Any = None,
        crawler: Any = None,
    ):
        """Initialize research agent."""
        self.llm = llm
        self.searcher = searcher
        self.crawler = crawler

    async def research(
        self,
        topic: str,
        depth: str = "medium"
    ) -> Dict[str, Any]:
        """Conduct autonomous research."""
        if depth == "deep":
            max_sources = 10
            max_results = 20
        elif depth == "paranoid":
            max_sources = 20
            max_results = 50
        else:
            max_sources = 3
            max_results = 5

        from tools.web_search import WebSearch
        from tools.web_crawler import WebCrawler

        searcher = self.searcher or WebSearch()
        crawler = self.crawler or WebCrawler()

        sources = searcher.search(topic, max_results=max_results)

        content = {}
        for source in sources[:max_sources]:
            try:
                page = crawler.fetch_page(source.url)
                if page:
                    content[source.url] = page.text[:5000]
            except Exception:
                pass

        prompt = f"""Research report on: {topic}

Based on {len(content)} sources, provide:
1. Executive summary
2. Key findings
3. Important details
4. Recommendations
5. Sources cited

Format as a comprehensive research report."""

        messages = [
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": prompt}
        ]

        report = await self.llm.async_chat(messages)

        return {
            "topic": topic,
            "depth": depth,
            "sources_count": len(content),
            "report": report,
            "sources": list(content.keys()),
        }


class AgentOrchestrator:
    """Orchestrates all PHANTOM agents."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize orchestrator."""
        self.config = config or Config.get_instance()
        self.llm = LLMBackend(self.config)
        self.memory = ConversationMemory(self.config)

        self.autonomous = AutonomousAgent(self.config, self.llm, self.memory)
        self.code_gen = CodeGenerator(self.llm)
        self.research = ResearchAgent(self.llm)

    async def complete_objective(
        self,
        objective: str,
        auto_execute: bool = True
    ) -> Dict[str, Any]:
        """Complete a complex objective autonomously."""
        return await self.autonomous.run_objective(objective, auto_execute)

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "tasks_queue": len(self.autonomous._task_queue),
            "tasks_completed": len(self.autonomous._completed_tasks),
            "capabilities": list(self.autonomous.CAPABILITIES.keys()),
        }