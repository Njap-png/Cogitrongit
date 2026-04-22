"""PHANTOM Self-Learning Engine - Learns from every interaction."""

import json
import re
import time
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, Counter
import threading

from core.config import Config
from core.memory import ConversationMemory
from core.llm import LLMBackend

import logging

logger = logging.getLogger("phantom.learner")

@dataclass
class LearnedConcept:
    """A concept PHANTOM has learned."""
    topic: str
    key_facts: List[str]
    confidence: float
    source_type: str
    learned_at: str
    access_count: int
    last_accessed: str
    related_topics: List[str]

@dataclass
class LearningResult:
    """Result of a learning operation."""
    success: bool
    concepts_learned: int
    confidence: float
    details: str

@dataclass
class SkillProgress:
    """Progress in learning a skill."""
    skill_name: str
    level: int
    experience_points: int
    required_points: int
    mastered: bool

class ConceptGraph:
    """Knowledge graph connecting concepts."""

    def __init__(self):
        """Initialize concept graph."""
        self.nodes: Dict[str, LearnedConcept] = {}
        self.edges: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.Lock()

    def add_concept(self, concept: LearnedConcept) -> None:
        """Add concept to graph."""
        with self._lock:
            self.nodes[concept.topic.lower()] = concept

            for related in concept.related_topics:
                self.edges[concept.topic.lower()].add(related.lower())
                self.edges[related.lower()].add(concept.topic.lower())

    def get_related(self, topic: str, depth: int = 1) -> List[str]:
        """Get related concepts."""
        topic_lower = topic.lower()
        related = set()

        if topic_lower not in self.edges:
            return []

        to_explore = [(topic_lower, 0)]
        explored = set()

        while to_explore:
            current, d = to_explore.pop(0)
            if current in explored or d > depth:
                continue

            explored.add(current)
            for neighbor in self.edges.get(current, set()):
                related.add(neighbor)
                if d < depth:
                    to_explore.append((neighbor, d + 1))

        return list(related)

    def search(self, query: str) -> List[Tuple[str, float]]:
        """Search concepts by relevance."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []

        for topic, concept in self.nodes.items():
            score = 0.0

            if query_lower in topic:
                score += 1.0
            elif query_lower in concept.key_facts:
                score += 0.8

            topic_words = set(topic.lower().split())
            common = query_words & topic_words
            score += len(common) * 0.2

            for fact in concept.key_facts:
                fact_words = set(fact.lower().split())
                if common & fact_words:
                    score += 0.1

            if score > 0:
                concept.access_count += 1
                concept.last_accessed = datetime.now().isoformat()
                results.append((topic, score))

        return sorted(results, key=lambda x: x[1], reverse=True)


class Learner:
    """Self-learning engine that makes PHANTOM smarter."""

    SKILL_TREE = {
        "reconnaissance": {
            "osint": 0,
            "port_scanning": 0,
            "subdomain_enum": 0,
            "service_detection": 0,
        },
        "web_security": {
            "sql_injection": 0,
            "xss": 0,
            "csrf": 0,
            "ssrf": 0,
            "idor": 0,
            "api_testing": 0,
        },
        "cryptography": {
            "encoding": 0,
            "encryption": 0,
            "hashing": 0,
            "key_exchange": 0,
        },
        "privilege_escalation": {
            "linux_privesc": 0,
            "windows_privesc": 0,
            "container_escape": 0,
        },
        "network_pivoting": {
            "tunneling": 0,
            "port_forwarding": 0,
            "proxychains": 0,
        },
        "malware_analysis": {
            "static_analysis": 0,
            "dynamic_analysis": 0,
            "decompilation": 0,
        },
    }

    XP_PER_LEVEL = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500]

    def __init__(
        self,
        config: Optional[Config] = None,
        memory: Optional[ConversationMemory] = None,
        llm: Optional[LLMBackend] = None
    ):
        """Initialize learner."""
        self.config = config or Config.get_instance()
        self.memory = memory or ConversationMemory(self.config)
        self.llm = llm or LLMBackend(self.config)

        self.concept_graph = ConceptGraph()
        self.skills: Dict[str, SkillProgress] = {}
        self._learned_topics: Set[str] = set()

        self._init_skills()
        self._load_knowledge()

    def _init_skills(self) -> None:
        """Initialize skill tree from memory."""
        skills_file = self.config.config_dir / "memory" / "skills.json"

        if skills_file.exists():
            try:
                with open(skills_file) as f:
                    data = json.load(f)
                    for skill_name, skill_data in data.items():
                        self.skills[skill_name] = SkillProgress(
                            skill_name=skill_name,
                            level=skill_data.get("level", 0),
                            experience_points=skill_data.get("xp", 0),
                            required_points=self.XP_PER_LEVEL[skill_data.get("level", 0)],
                            mastered=skill_data.get("level", 0) >= 10
                        )
            except Exception as e:
                logger.debug(f"Failed to load skills: {e}")

        for category, skills in self.SKILL_TREE.items():
            for skill_name in skills:
                full_name = f"{category}.{skill_name}"
                if full_name not in self.skills:
                    self.skills[full_name] = SkillProgress(
                        skill_name=full_name,
                        level=0,
                        experience_points=0,
                        required_points=self.XP_PER_LEVEL[0],
                        mastered=False
                    )

    def _load_knowledge(self) -> None:
        """Load learned concepts from disk."""
        kb_dir = self.config.config_dir / "memory"
        concepts_file = kb_dir / "concepts.json"

        if concepts_file.exists():
            try:
                with open(concepts_file) as f:
                    data = json.load(f)

                for topic, concept_data in data.items():
                    concept = LearnedConcept(
                        topic=topic,
                        key_facts=concept_data.get("facts", []),
                        confidence=concept_data.get("confidence", 0.5),
                        source_type=concept_data.get("source", "unknown"),
                        learned_at=concept_data.get("learned_at", ""),
                        access_count=concept_data.get("access_count", 0),
                        last_accessed=concept_data.get("last_accessed", ""),
                        related_topics=concept_data.get("related", [])
                    )
                    self.concept_graph.add_concept(concept)
                    self._learned_topics.add(topic.lower())
            except Exception as e:
                logger.debug(f"Failed to load knowledge: {e}")

    def _save_knowledge(self) -> None:
        """Persist learned concepts."""
        kb_dir = self.config.config_dir / "memory"
        kb_dir.mkdir(parents=True, exist_ok=True)
        concepts_file = kb_dir / "concepts.json"

        data = {}
        for topic, concept in self.concept_graph.nodes.items():
            data[topic] = {
                "facts": concept.key_facts,
                "confidence": concept.confidence,
                "source": concept.source_type,
                "learned_at": concept.learned_at,
                "access_count": concept.access_count,
                "last_accessed": concept.last_accessed,
                "related": list(concept.related_topics),
            }

        with open(concepts_file, "w") as f:
            json.dump(data, f, indent=2)

    def _save_skills(self) -> None:
        """Persist skill progress."""
        skills_file = self.config.config_dir / "memory" / "skills.json"

        data = {}
        for skill_name, skill in self.skills.items():
            data[skill_name] = {
                "level": skill.level,
                "xp": skill.experience_points,
            }

        with open(skills_file, "w") as f:
            json.dump(data, f, indent=2)

    def learn_from_response(
        self,
        query: str,
        response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LearningResult:
        """Learn from a response to a query."""
        learned = 0
        topics_found = []

        patterns = {
            "cve": r"CVE-\d{4}-\d{4,}",
            "tool": r"\b(nmap|metasploit|burp|sqlmap|gobuster|john|hashcat|aircrack)\b",
            "technique": r"\b(sqli|xss|csrf|ssrf|idor|lfi|rfi|xxe)\b",
            "os": r"\b(kali|parrot|debian|ubuntu|centos|windows|macos)\b",
            "protocol": r"\b(http|https|ssh|ftp|smb|dns|ldap|smtp)\b",
            "port": r"\bport[s]?\s*:?\s*(\d+,?\s*)+",
            "encoding": r"\b(base64|base32|hex|rot13|url)\b",
        }

        for pattern_type, pattern in patterns.items():
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                for match in set(matches):
                    if self._add_fact(pattern_type, str(match).upper(), response):
                        learned += 1
                        topics_found.append(str(match))

        for topic in topics_found:
            related = self._find_related_concepts(topic)
            concept = self.concept_graph.nodes.get(topic.lower())
            if concept:
                concept.related_topics.extend(related)
                concept.related_topics = list(set(concept.related_topics))

        self._save_knowledge()

        logger.info(f"Learned {learned} new facts from response")

        return LearningResult(
            success=learned > 0,
            concepts_learned=learned,
            confidence=min(1.0, learned / 10.0),
            details=f"Found topics: {topics_found}"
        )

    def _add_fact(self, category: str, fact: str, context: str) -> bool:
        """Add a fact to knowledge base."""
        fact_lower = fact.lower()

        if fact_lower in self._learned_topics:
            concept = self.concept_graph.nodes.get(fact_lower)
            if concept:
                concept.access_count += 1
                concept.last_accessed = datetime.now().isoformat()
            return False

        concept = LearnedConcept(
            topic=fact,
            key_facts=[context[:500]],
            confidence=0.7,
            source_type=category,
            learned_at=datetime.now().isoformat(),
            access_count=1,
            last_accessed=datetime.now().isoformat(),
            related_topics=[]
        )

        self.concept_graph.add_concept(concept)
        self._learned_topics.add(fact_lower)

        return True

    def _find_related_concepts(self, topic: str) -> List[str]:
        """Find related concepts."""
        related = self.concept_graph.get_related(topic, depth=1)
        return related[:5]

    def learn_from_web(
        self,
        topic: str,
        search_results: List[Dict[str, Any]]
    ) -> LearningResult:
        """Learn from web search results."""
        learned = 0
        facts = []

        for result in search_results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            url = result.get("url", "")

            if title and len(title) > 5:
                fact = f"{title}: {snippet[:300]}"
                facts.append(fact)
                learned += 1

        for i, fact in enumerate(facts[:5]):
            category = "web_search"
            if self._add_fact(category, f"WEB_{topic}_{i}", fact):
                pass

        self._update_skill(topic, xp_gain=learned * 5)

        self._save_knowledge()

        return LearningResult(
            success=learned > 0,
            concepts_learned=learned,
            confidence=min(1.0, learned / 5.0),
            details=f"Learned {learned} facts about {topic}"
        )

    def learn_from_code(
        self,
        code: str,
        language: str = "unknown"
    ) -> LearningResult:
        """Analyze and learn from code."""
        functions = re.findall(r"def\s+(\w+)", code)
        classes = re.findall(r"class\s+(\w+)", code)
        imports = re.findall(r"import\s+(\w+)", code)
        api_calls = re.findall(r"(\w+)\.(\w+)\(", code)

        learned = 0

        for func in functions[:10]:
            if self._add_fact("function", func, f"Language: {language}"):
                learned += 1

        for cls in classes[:5]:
            if self._add_fact("class", cls, f"Language: {language}"):
                learned += 1

        for imp in imports[:10]:
            if self._add_fact("import", imp, f"Language: {language}"):
                learned += 1

        for api_call in api_calls[:10]:
            if self._add_fact("api", f"{api_call[0]}.{api_call[1]}", f"Language: {language}"):
                learned += 1

        self._save_knowledge()

        return LearningResult(
            success=learned > 0,
            concepts_learned=learned,
            confidence=min(1.0, learned / 20.0),
            details=f"Extracted {learned} concepts from {language} code"
        )

    def learn_from_error(
        self,
        error: str,
        context: str = ""
    ) -> LearningResult:
        """Learn from errors and failures."""
        error_type = "UnknownError"

        error_patterns = {
            "ImportError": r"ImportError",
            "SyntaxError": r"SyntaxError",
            "PermissionError": r"PermissionError",
            "TimeoutError": r"TimeoutError",
            "ConnectionError": r"ConnectionError",
            "AuthenticationError": r"(Auth|authentication|login)",
            "SQLInjection": r"(SQL|sqli|injection)",
        }

        for error_name, pattern in error_patterns.items():
            if re.search(pattern, error, re.IGNORECASE):
                error_type = error_name
                break

        fact = f"Error {error_type}: {error[:200]}"
        if context:
            fact += f" | Context: {context[:200]}"

        self._add_fact("error", error_type, fact)

        self._save_knowledge()

        return LearningResult(
            success=True,
            concepts_learned=1,
            confidence=0.8,
            details=f"Learned from {error_type}"
        )

    def _update_skill(self, skill_name: str, xp_gain: int) -> bool:
        """Update skill experience."""
        if skill_name not in self.skills:
            self.skills[skill_name] = SkillProgress(
                skill_name=skill_name,
                level=0,
                experience_points=0,
                required_points=self.XP_PER_LEVEL[0],
                mastered=False
            )

        skill = self.skills[skill_name]
        skill.experience_points += xp_gain

        while skill.level < 10 and skill.experience_points >= skill.required_points:
            skill.level += 1
            skill.required_points = self.XP_PER_LEVEL[skill.level]

        skill.mastered = skill.level >= 10

        self._save_skills()

        return skill.mastered

    def get_skill_level(self, skill_name: str) -> SkillProgress:
        """Get progress on a skill."""
        return self.skills.get(skill_name, SkillProgress(
            skill_name=skill_name,
            level=0,
            experience_points=0,
            required_points=self.XP_PER_LEVEL[0],
            mastered=False
        ))

    def get_all_skills(self) -> Dict[str, SkillProgress]:
        """Get all skill progress."""
        return self.skills

    def search_knowledge(self, query: str, top_k: int = 5) -> List[LearnedConcept]:
        """Search learned knowledge."""
        results = self.concept_graph.search(query)

        concepts = []
        for topic, score in results[:top_k]:
            if topic in self.concept_graph.nodes:
                concepts.append(self.concept_graph.nodes[topic])

        return concepts

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge statistics."""
        total_concepts = len(self.concept_graph.nodes)
        by_category = Counter()

        for concept in self.concept_graph.nodes.values():
            by_category[concept.source_type] += 1

        skill_summary = {}
        for skill_name, skill in self.skills.items():
            if skill.level > 0:
                skill_summary[skill_name] = {
                    "level": skill.level,
                    "xp": skill.experience_points,
                    "mastered": skill.mastered,
                }

        return {
            "total_concepts": total_concepts,
            "by_category": dict(by_category),
            "skills_learned": len(skill_summary),
            "skill_progress": skill_summary,
        }

    def export_knowledge(self, path: str) -> str:
        """Export all knowledge to file."""
        output_file = Path(path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write("# PHANTOM Knowledge Base\n\n")

            for topic, concept in sorted(self.concept_graph.nodes.items()):
                f.write(f"## {concept.topic}\n\n")
                f.write(f"- Confidence: {concept.confidence:.0%}\n")
                f.write(f"- Source: {concept.source_type}\n")
                f.write(f"- Learned: {concept.learned_at[:10]}\n")
                f.write(f"- Times accessed: {concept.access_count}\n\n")
                f.write("### Facts\n\n")
                for fact in concept.key_facts:
                    f.write(f"- {fact}\n")
                if concept.related_topics:
                    f.write("\n### Related\n\n")
                    for related in concept.related_topics:
                        f.write(f"- [[{related}]]\n")
                f.write("\n---\n\n")

        return str(output_file)


class SelfLearning:
    """Static access to self-learning features."""

    @staticmethod
    def get_learner(config: Optional[Config] = None) -> Learner:
        """Get learner instance."""
        return Learner(config=config)

    @staticmethod
    def learn(query: str, response: str) -> LearningResult:
        """Quick learn from response."""
        return Learner().learn_from_response(query, response)

    @staticmethod
    def search(query: str) -> List[LearnedConcept]:
        """Quick search knowledge."""
        return Learner().search_knowledge(query)

    @staticmethod
    def stats() -> Dict[str, Any]:
        """Get learning statistics."""
        return Learner().get_knowledge_stats()