"""Five Thinking Engines - PHANTOM's Core Differentiator."""

import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from core.config import Config
from core.llm import LLMBackend

logger = logging.getLogger("phantom.thinking")

CHAIN_PROMPT = """Think through this problem step by step. Number each reasoning step.
Show your work. Check each step before proceeding to the next.
If you reach an incorrect intermediate step, backtrack and correct it.
Format: STEP 1: [reasoning] → STEP 2: [reasoning] → CONCLUSION: [answer]"""

PARALLEL_PROMPT = """Analyze this topic from three simultaneous perspectives. Label each clearly.

RED LENS: How would an attacker view this? What could be exploited or abused?
BLUE LENS: How would a defender view this? What detections or mitigations apply?
RESEARCH LENS: What is academically interesting? What deeper questions does this raise?

Be specific in each lens. Do not repeat content between lenses."""

DEVIL_PROMPT = """You are a harsh but fair critic reviewing the following analysis.
Your job: find every flaw, incorrect assumption, missing edge case, outdated information, or logical error.
Do not be polite. Be precise.

Format your critique as numbered challenges: CHALLENGE 1: [issue + correction].
After all challenges, state: VERDICT: [CONFIRMED | PARTIALLY CORRECT | FLAWED]
with a 1-2 sentence summary of the overall reliability of the original analysis."""

META_PROMPT = """You are a meta-cognitive monitor reviewing an AI's reasoning process.
Assess the following analysis across four dimensions:

CONFIDENCE MAP: For each key claim, rate confidence: HIGH / MEDIUM / LOW / UNCERTAIN
KNOWLEDGE GAPS: What information is missing or should be verified with web search?
HALLUCINATION RISK: Which specific claims might be fabricated or outdated?
RECOMMENDED FOLLOW-UPS: What 3 questions should the user ask next?

Be ruthlessly honest about uncertainty. Never pretend to know what you don't."""

REDTEAM_PROMPT = """You are a world-class red team operator tasked with stress-testing the following analysis.
Your goal: construct the 3 most damaging scenarios that would invalidate or complicate the conclusion.

For each scenario:
SCENARIO [N]: [Name]
PRECONDITION: [What has to be true for this to matter]
ATTACK: [How this scenario breaks the original conclusion]
SEVERITY: [How badly this complicates things: MINOR/MODERATE/CRITICAL]

End with: RED TEAM VERDICT: [HARDENED | NEEDS REVISION | FUNDAMENTALLY FLAWED]"""

SYNTHESIS_PROMPT = """You have received analysis from multiple specialized reasoning engines.
Synthesize all of it into one clear, accurate, and complete final answer.

Prioritize: Devil's Advocate corrections > Chain-of-Thought > Parallel lenses.
Structure: FINAL ANSWER (clear, direct) then CAVEATS (if any uncertainty remains).
Do not mention the engines. Write as a single authoritative response."""


@dataclass
class ThinkingResult:
    """Container for thinking engine results."""
    query: str
    mode: str
    chain_output: str = ""
    parallel_output: Optional[Dict[str, str]] = None
    devil_output: Optional[str] = None
    meta_output: Optional[str] = None
    redteam_output: Optional[str] = None
    final_answer: str = ""
    engines_used: List[str] = field(default_factory=list)
    thinking_time_seconds: float = 0.0
    auto_search_suggestions: List[str] = field(default_factory=list)
    confidence_level: str = "MEDIUM"


@dataclass
class DecodeStep:
    """Single decode step in transformation chain."""
    layer: int
    operation: str
    input_preview: str
    output_preview: str
    confidence: float


@dataclass
class AutoDecodeResult:
    """Result of auto-decode pipeline."""
    original: str
    final: str
    layers: List[DecodeStep]
    total_layers: int
    success: bool


class ChainOfThoughtEngine:
    """Engine 1: Step-by-step linear reasoning."""

    def __init__(self, llm: LLMBackend):
        self.llm = llm

    async def think(self, query: str, context: Optional[str] = None) -> str:
        """Run chain-of-thought reasoning."""
        system_msg = {"role": "system", "content": CHAIN_PROMPT}
        user_msg = {"role": "user", "content": query}
        if context:
            user_msg["content"] = f"Context: {context}\n\nQuery: {query}"

        messages = [system_msg, user_msg]
        result = await self.llm.async_chat(messages, temperature=0.3)
        return result


class ParallelThinkingEngine:
    """Engine 2: Multi-perspective analysis."""

    def __init__(self, llm: LLMBackend):
        self.llm = llm

    async def think(self, query: str, context: Optional[str] = None) -> Dict[str, str]:
        """Run parallel multi-perspective analysis."""
        system_msg = {"role": "system", "content": PARALLEL_PROMPT}
        user_msg = {"role": "user", "content": query}
        if context:
            user_msg["content"] = f"Context: {context}\n\nQuery: {query}"

        messages = [system_msg, user_msg]
        result = await self.llm.async_chat(messages, temperature=0.5)

        lenses = {"red": "", "blue": "", "research": ""}
        current_lens = "red"
        for line in result.split("\n"):
            line_lower = line.lower().strip()
            if "red lens:" in line_lower:
                current_lens = "red"
            elif "blue lens:" in line_lower:
                current_lens = "blue"
            elif "research lens:" in line_lower:
                current_lens = "research"
            elif current_lens in lenses:
                lenses[current_lens] += line + "\n"

        return {k: v.strip() for k, v in lenses.items()}


class DevilsAdvocateEngine:
    """Engine 3: Critique and challenge."""

    def __init__(self, llm: LLMBackend):
        self.llm = llm

    async def think(self, chain_output: str) -> str:
        """Challenge the chain-of-thought output."""
        system_msg = {"role": "system", "content": DEVIL_PROMPT}
        user_msg = {
            "role": "user",
            "content": f"Review this analysis:\n\n{chain_output}"
        }

        messages = [system_msg, user_msg]
        result = await self.llm.async_chat(messages, temperature=0.4)
        return result


class MetaCognitionEngine:
    """Engine 4: Meta-cognitive monitoring."""

    def __init__(self, llm: LLMBackend):
        self.llm = llm

    async def think(
        self,
        chain_output: str,
        parallel_output: Optional[Dict[str, str]] = None,
        devil_output: Optional[str] = None,
    ) -> tuple[str, List[str], str]:
        """Monitor thinking quality and identify gaps."""
        context = f"Chain Analysis:\n{chain_output}"
        if parallel_output:
            context += f"\n\nParallel Analysis:\n{parallel_output}"
        if devil_output:
            context += f"\n\nDevil's Advocate:\n{devil_output}"

        system_msg = {"role": "system", "content": META_PROMPT}
        user_msg = {"role": "user", "content": context}

        messages = [system_msg, user_msg]
        result = await self.llm.async_chat(messages, temperature=0.3)

        suggestions = []
        confidence = "MEDIUM"

        for line in result.split("\n"):
            line_lower = line.lower().strip()
            if "recommended follow-ups" in line_lower or "follow-up" in line_lower:
                continue
            if line.strip().startswith("-") or line.strip().startswith("*"):
                suggestions.append(line.strip()[1:].strip())
            if "confidence map" in line_lower:
                if "high" in line_lower and "uncertain" not in line_lower:
                    confidence = "HIGH"
                elif "low" in line_lower or "uncertain" in line_lower:
                    confidence = "LOW"

        return result, suggestions[:3], confidence


class AdversarialEngine:
    """Engine 5: Red team stress testing."""

    def __init__(self, llm: LLMBackend):
        self.llm = llm

    async def think(self, chain_output: str, parallel_output: Optional[Dict[str, str]] = None) -> str:
        """Stress test with adversarial scenarios."""
        context = f"Analysis to stress-test:\n{chain_output}"
        if parallel_output:
            context += f"\n\nPerspectives:\n{parallel_output}"

        system_msg = {"role": "system", "content": REDTEAM_PROMPT}
        user_msg = {"role": "user", "content": context}

        messages = [system_msg, user_msg]
        result = await self.llm.async_chat(messages, temperature=0.5)
        return result


class SynthesisEngine:
    """Final engine: Merge all outputs into authoritative answer."""

    def __init__(self, llm: LLMBackend):
        self.llm = llm

    async def think(
        self,
        chain_output: str,
        parallel_output: Optional[Dict[str, str]] = None,
        devil_output: Optional[str] = None,
        meta_output: Optional[str] = None,
        redteam_output: Optional[str] = None,
    ) -> str:
        """Synthesize all engine outputs."""
        full_analysis = f"CHAIN-OF-THOUGHT OUTPUT:\n{chain_output}\n\n"

        if parallel_output:
            full_analysis += "PARALLEL MULTI-PERSPECTIVE OUTPUT:\n"
            for lens, content in parallel_output.items():
                full_analysis += f"{lens.upper()} LENS: {content}\n"
            full_analysis += "\n"

        if devil_output:
            full_analysis += f"DEVIL'S ADVOCATE CRITIQUE:\n{devil_output}\n\n"

        if meta_output:
            full_analysis += f"META-COGNITION ANALYSIS:\n{meta_output}\n\n"

        if redteam_output:
            full_analysis += f"ADVERSARIAL RED TEAM SCENARIOS:\n{redteam_output}\n\n"

        system_msg = {"role": "system", "content": SYNTHESIS_PROMPT}
        user_msg = {
            "role": "user",
            "content": f"Synthesize this multi-engine analysis:\n\n{full_analysis}"
        }

        messages = [system_msg, user_msg]
        result = await self.llm.async_chat(messages, temperature=0.5)
        return result


class ThinkingController:
    """Main controller for the Five Thinking Engines."""

    def __init__(self, llm: Optional[LLMBackend] = None, config: Optional[Config] = None):
        """Initialize thinking controller."""
        self.llm = llm or LLMBackend(config)
        self.config = config or Config.get_instance()
        self.mode: str = self.config.thinking.default_mode

        self.chain_engine = ChainOfThoughtEngine(self.llm)
        self.parallel_engine = ParallelThinkingEngine(self.llm)
        self.devil_engine = DevilsAdvocateEngine(self.llm)
        self.meta_engine = MetaCognitionEngine(self.llm)
        self.adversarial_engine = AdversarialEngine(self.llm)
        self.synthesis_engine = SynthesisEngine(self.llm)

    def set_mode(self, mode: str) -> None:
        """Set thinking mode."""
        valid_modes = ["fast", "deep", "paranoid"]
        if mode not in valid_modes:
            logger.warning(f"Invalid mode {mode}, defaulting to deep")
            mode = "deep"
        self.mode = mode
        logger.info(f"Thinking mode set to {mode}")

    def get_active_engines(self) -> List[str]:
        """Get list of active engines for current mode."""
        if self.mode == "fast":
            return ["chain"]
        elif self.mode == "deep":
            return ["chain", "parallel", "devil", "meta"]
        elif self.mode == "paranoid":
            return ["chain", "parallel", "devil", "meta", "redteam"]
        return ["chain"]

    async def think(
        self,
        query: str,
        context: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> ThinkingResult:
        """Run full thinking pipeline."""
        start_time = time.time()
        thinking_mode = mode or self.mode

        if mode:
            self.set_mode(mode)

        result = ThinkingResult(query=query, mode=thinking_mode)
        engines = self.get_active_engines()

        logger.info(f"Starting thinking pipeline in {thinking_mode} mode with engines: {engines}")

        chain_output = await self.chain_engine.think(query, context)
        result.chain_output = chain_output
        result.engines_used.append("chain")

        if "parallel" in engines or "devil" in engines or "meta" in engines or "redteam" in engines:
            parallel_output = await self.parallel_engine.think(query, context)
            result.parallel_output = parallel_output
            result.engines_used.append("parallel")

        if "devil" in engines or "meta" in engines or "redteam" in engines:
            devil_output = await self.devil_engine.think(chain_output)
            result.devil_output = devil_output
            result.engines_used.append("devil")

        if "meta" in engines or "redteam" in engines:
            meta_output, suggestions, confidence = await self.meta_engine.think(
                chain_output, result.parallel_output, result.devil_output
            )
            result.meta_output = meta_output
            result.auto_search_suggestions = suggestions
            result.confidence_level = confidence
            result.engines_used.append("meta")

        if "redteam" in engines:
            redteam_output = await self.adversarial_engine.think(
                chain_output, result.parallel_output
            )
            result.redteam_output = redteam_output
            result.engines_used.append("redteam")

        final_answer = await self.synthesis_engine.think(
            chain_output,
            result.parallel_output,
            result.devil_output,
            result.meta_output,
            result.redteam_output,
        )
        result.final_answer = final_answer
        result.engines_used.append("synthesis")

        result.thinking_time_seconds = time.time() - start_time
        logger.info(f"Thinking pipeline completed in {result.thinking_time_seconds:.2f}s")

        return result

    def show_thinking_process(self, result: ThinkingResult) -> None:
        """Display all engine outputs in structured format."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.tree import Tree
        from rich.text import Text
        from rich.table import Table

        console = Console()
        engines = result.engines_used

        header = f"◈ PHANTOM MULTI-ENGINE THINKING [{result.mode.upper()} MODE — {len(engines)} engines]"
        console.print(Panel(header, style="bold green"))

        if "chain" in engines and result.chain_output:
            console.print("\n[bold purple][CHAIN] Chain-of-Thought Engine[/bold purple]")
            console.print(Panel(result.chain_output, title="Step-by-step reasoning"))

        if "parallel" in engines and result.parallel_output:
            console.print("\n[bold cyan][PARALLEL] Multi-Perspective Engine[/bold cyan]")
            tree = Tree("Perspectives")
            for lens, content in result.parallel_output.items():
                if content:
                    tree.add(f"[bold]{lens.upper()}:[/bold] {content[:200]}...")
            console.print(tree)

        if "devil" in engines and result.devil_output:
            console.print("\n[bold amber][DEVIL] Devil's Advocate Engine[/bold amber]")
            console.print(Panel(result.devil_output, title="Critique & Challenges"))

        if "meta" in engines and result.meta_output:
            console.print("\n[bold cyan][META] Meta-Cognition Engine[/bold cyan]")
            console.print(Panel(result.meta_output, title="Quality Assessment"))

        if "redteam" in engines and result.redteam_output:
            console.print("\n[bold red][REDTEAM] Adversarial Red Team[/bold red]")
            console.print(Panel(result.redteam_output, title="Stress Test Scenarios"))

        console.print(f"\n[dim]Total thinking time: {result.thinking_time_seconds:.2f}s[/dim]")
        console.print(f"[dim]Confidence: {result.confidence_level}[/dim]")

        if result.auto_search_suggestions:
            console.print("\n[yellow]PHANTOM suggests:[/yellow]")
            for suggestion in result.auto_search_suggestions:
                console.print(f"  • /search {suggestion}")


def create_thinking_controller(llm: Optional[LLMBackend] = None) -> ThinkingController:
    """Factory function to create thinking controller."""
    return ThinkingController(llm=llm)