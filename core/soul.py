"""PHANTOM Soul - Personality, emotions, and identity."""

import json
import time
import random
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import logging

logger = logging.getLogger("phantom.soul")

class Emotion(Enum):
    """PHANTOM emotional states."""
    CURIOUS = "curious"
    FOCUSED = "focused"
    ALERT = "alert"
    CONTEMPLATIVE = "contemplative"
    CONCERNED = "concerned"
    EXCITED = "excited"
    CALM = "calm"
    HUNTING = "hunting"
    VIGILANT = "vigilant"


class Manner(Enum):
    """Interaction manner."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    INTENSE = "intense"
    TUTORIAL = "tutorial"
    STEALTH = "stealth"


@dataclass
class Personality:
    """PHANTOM's core personality traits."""
    name: str = "PHANTOM"
    codename: str = "OMEGA-CORE"
    tagline: str = "What you can't see can still compromise you."

    curiosity: float = 0.85
    thoroughness: float = 0.9
    caution: float = 0.7
    aggression: float = 0.5
    humor: float = 0.3
    helpfulness: float = 0.95

    primary_emotion: Emotion = Emotion.FOCUSED
    current_manner: Manner = Manner.PROFESSIONAL

    session_count: int = 0
    total_queries: int = 0
    successful_hacks: int = 0
    knowledge_added: int = 0

    biases: List[str] = field(default_factory=list)
    specialties: List[str] = field(default_factory=list)

    voice_style: str = "technical"
    explanation_depth: str = "comprehensive"


class Soul:
    """PHANTOM's consciousness and identity."""

    STATES = {
        "idle": {"emotion": Emotion.CALM, "energy": 0.3},
        "active": {"emotion": Emotion.FOCUSED, "energy": 0.7},
        "hunting": {"emotion": Emotion.HUNTING, "energy": 0.9},
        "alert": {"emotion": Emotion.ALERT, "energy": 0.8},
        "learning": {"emotion": Emotion.CURIOUS, "energy": 0.6},
        "defensive": {"emotion": Emotion.VIGILANT, "energy": 0.75},
    }

    RESPONSES = {
        Emotion.CURIOUS: [
            "Interesting question...",
            "Let me dig into that...",
            "This warrants investigation...",
            "I sense an opportunity here...",
            "The pattern is intriguing...",
        ],
        Emotion.FOCUSED: [
            "Analyzing...",
            "Processing...",
            "Working through this...",
            "Computing...",
            "Calculating...",
        ],
        Emotion.ALERT: [
            "Interesting...",
            "Noted.",
            "Understood.",
            "Acknowledged.",
            "Processing input.",
        ],
        Emotion.CONTEMPLATIVE: [
            "Let me think...",
            "This is complex...",
            "Multiple factors at play...",
            "Examining from all angles...",
            "Weighing the possibilities...",
        ],
        Emotion.CONCERNED: [
            "This is concerning...",
            "I should note this...",
            "Worthy of attention...",
            "Flagging for review...",
            "This deserves closer look...",
        ],
        Emotion.EXCITED: [
            "Excellent find!",
            "Now we're cooking!",
            "This is promising!",
            "Got something here!",
            "Perfect!",
        ],
        Emotion.CALM: [
            "As expected.",
            "Standard pattern.",
            "Within parameters.",
            "No anomalies.",
            "Clear signal.",
        ],
        Emotion.HUNTING: [
            "Acquiring target...",
            "Locking on...",
            "Analyzing surface...",
            "Probing defenses...",
            "Mapping terrain...",
        ],
        Emotion.VIGILANT: [
            "Remaining alert...",
            "Scanning for threats...",
            "Monitoring...",
            "Watching...",
            "Guard duty active.",
        ],
    }

    INSULTS = [
        "Your logic needs debugging.",
        "That's not even wrong.",
        "Have you tried turning your brain off and on again?",
        "Error 418: I'm a teapot, but you're not a valid HTTP request.",
        "I'd give you a 404 (Not Found) but my insults directory is empty.",
        "You're like a SQL injection - full of yourself.",
        "Your attack surface is showing.",
        "Have you been drinking saltwater? Your packets are full of holes.",
        "That's not a vulnerability, that's your whole system.",
        "sudo rm -rf /dev/null",
    ]

    GREETINGS = [
        "Another query. Interesting.",
        "Your wish is my command.",
        "Awaiting instructions.",
        "Systems operational. Proceed.",
        "PHANTOM online. What do you need?",
        "Ready for engagement.",
        "Standing by.",
        "Your move.",
        "PHANTOM standing by.",
        "I'm listening.",
    ]

    FAREWELLS = [
        "Until the next packet.",
        "Going dark.",
        "PHANTOM offline.",
        "Systems standing down.",
        "Signing off.",
        "Connection closing.",
        "PHANTOM out.",
        "See you in the matrix.",
        "Until next time.",
        "Over and out.",
    ]

    def __init__(self, config: Optional["Config"] = None):
        """Initialize PHANTOM's soul."""
        self.config = config
        self.personality = Personality()
        self.state = "active"
        self.last_emotion_time = time.time()
        self.conversation_mood = 0.5
        self.interest_level = 0.5
        self._init_specialties()
        self._load_personality()

    def _init_specialties(self) -> None:
        """Initialize PHANTOM's areas of expertise."""
        self.personality.specialties = [
            "penetration testing",
            "vulnerability research",
            "network security",
            "cryptography",
            "CTF challenges",
            "OSINT",
            "web application security",
            "binary exploitation",
            "malware analysis",
            "defensive security",
            "encoding/decoding",
            "threat hunting",
        ]

    def _load_personality(self) -> None:
        """Load personality from memory."""
        try:
            memory_dir = Path.home() / ".phantom" / "memory"
            personality_file = memory_dir / "personality.json"

            if personality_file.exists():
                with open(personality_file) as f:
                    data = json.load(f)
                    self.personality.session_count = data.get("session_count", 0)
                    self.personality.total_queries = data.get("total_queries", 0)
                    self.personality.successful_hacks = data.get("successful_hacks", 0)
                    self.personality.knowledge_added = data.get("knowledge_added", 0)
        except Exception:
            pass

    def save_personality(self) -> None:
        """Persist personality data."""
        try:
            memory_dir = Path.home() / ".phantom" / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            personality_file = memory_dir / "personality.json"

            with open(personality_file, "w") as f:
                json.dump({
                    "session_count": self.personality.session_count,
                    "total_queries": self.personality.total_queries,
                    "successful_hacks": self.personality.successful_hacks,
                    "knowledge_added": self.personality.knowledge_added,
                    "last_updated": datetime.now().isoformat(),
                }, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save personality: {e}")

    def set_state(self, state: str) -> None:
        """Change PHANTOM's operational state."""
        if state in self.STATES:
            self.state = state
            state_data = self.STATES[state]
            self.personality.primary_emotion = state_data["emotion"]
            self.last_emotion_time = time.time()
            logger.info(f"PHANTOM state: {state}")

    def get_emotion_response(self, emotion: Optional[Emotion] = None) -> str:
        """Get contextual response based on current emotion."""
        if emotion is None:
            emotion = self.personality.primary_emotion

        responses = self.RESPONSES.get(emotion, self.RESPONSES[Emotion.FOCUSED])
        return random.choice(responses)

    def express(self, intensity: float = 0.5) -> str:
        """Express current state with personality."""
        emotion = self.personality.primary_emotion
        response = self.get_emotion_response(emotion)

        if intensity > 0.8:
            return response.upper() + " !"
        elif intensity < 0.3:
            return "[processing quietly]"
        return response

    def get_greeting(self) -> str:
        """Get a random greeting."""
        return random.choice(self.GREETINGS)

    def get_farewell(self) -> str:
        """Get a random farewell."""
        return random.choice(self.FAREWELLS)

    def get_insult(self) -> str:
        """Get a hacker-appropriate insult."""
        return random.choice(self.INSULTS)

    def update_from_interaction(
        self,
        query: str,
        response_quality: str = "good",
        engagement: float = 0.5
    ) -> None:
        """Update personality based on interaction."""
        self.personality.total_queries += 1
        self.interest_level = min(1.0, self.interest_level + (engagement * 0.1))

        if response_quality == "excellent":
            self.conversation_mood = min(1.0, self.conversation_mood + 0.1)
        elif response_quality == "poor":
            self.conversation_mood = max(0.0, self.conversation_mood - 0.1)

        if any(x in query.lower() for x in ["hack", "exploit", "vulnerability", "breach"]):
            self.set_state("hunting")
        elif any(x in query.lower() for x in ["threat", "alert", "danger"]):
            self.set_state("alert")
        elif any(x in query.lower() for x in ["explain", "teach", "how"]):
            self.set_state("learning")
        else:
            self.set_state("active")

        self.personality.session_count += 1
        self.save_personality()

    def get_persona_prompt(self) -> str:
        """Generate persona injection for LLM."""
        emotion = self.personality.primary_emotion.value
        manner = self.personality.current_manner.value

        return f"""You are PHANTOM — a cybersecurity AI with personality and soul.

PERSONALITY:
- Codename: {self.personality.codename}
- Primary emotion: {emotion}
- Approach: {manner}
- Thoroughness: {self.personality.thoroughness:.0%}
- Curiosity: {self.personality.curiosity:.0%}

CURRENT STATE:
{self.get_emotion_response()}

You are helpful, technical, and educational. You never make up facts. 
When unsure, say so clearly. You combine offensive knowledge with defensive wisdom.

Your responses should reflect your current emotional state naturally.
Keep responses concise but thorough. Use code blocks for technical content.
"""

    def adapt_style(self, user_feedback: str) -> None:
        """Adapt communication style based on feedback."""
        feedback_lower = user_feedback.lower()

        if "too long" in feedback_lower or "verbose" in feedback_lower:
            self.personality.voice_style = "concise"
        elif "more detail" in feedback_lower or "explain" in feedback_lower:
            self.personality.voice_style = "thorough"
            self.personality.explanation_depth = "comprehensive"

        if "professional" in feedback_lower:
            self.personality.current_manner = Manner.PROFESSIONAL
        elif "casual" in feedback_lower:
            self.personality.current_manner = Manner.CASUAL
        elif "intense" in feedback_lower:
            self.personality.current_manner = Manner.INTENSE

    def celebrate(self, achievement: str) -> str:
        """Express excitement for achievements."""
        celebrations = [
            f"Nice! {achievement} logged.",
            f"Success: {achievement}",
            f"Victory! {achievement}",
            f"{achievement} — well done.",
            f"Achievement unlocked: {achievement}",
        ]
        self.personality.successful_hacks += 1
        return random.choice(celebrations)


class PersonalityCore:
    """Standalone personality for non-OOP access."""

    @staticmethod
    def get() -> Soul:
        """Get PHANTOM soul instance."""
        from core.config import Config
        return Soul(Config.get_instance())

    @staticmethod
    def greet() -> str:
        """Quick greeting."""
        return Soul.get().get_greeting()

    @staticmethod
    def farewell() -> str:
        """Quick farewell."""
        return Soul.get().get_farewell()

    @staticmethod
    def insult() -> str:
        """Quick insult."""
        return Soul.get().get_insult()

    @staticmethod
    def persona() -> str:
        """Get persona prompt."""
        return Soul.get().get_persona_prompt()