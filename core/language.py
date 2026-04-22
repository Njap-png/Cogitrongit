"""PHANTOM Language Learning - AI-powered language tutoring system."""

import json
import random
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from dataclasses import asdict

from core.config import Config

import logging

logger = logging.getLogger("phantom.language")


@dataclass
class Word:
    """Vocabulary word."""
    id: str
    word: str
    translation: str
    language: str
    romanization: str = ""
    part_of_speech: str = ""
    pronunciation: str = ""
    example_sentence: str = ""
    example_translation: str = ""
    difficulty: int = 1
    tags: List[str] = field(default_factory=list)
    learned: bool = False
    times_seen: int = 0
    times_correct: int = 0
    last_seen: str = ""
    next_review: str = ""
    ease_factor: float = 2.5
    interval: int = 1


@dataclass
class Phrase:
    """Common phrase or idiom."""
    id: str
    phrase: str
    translation: str
    language: str
    context: str = ""
    formality: str = "neutral"
    usage_notes: str = ""


@dataclass
class GrammarRule:
    """Grammar rule."""
    id: str
    rule: str
    explanation: str
    examples: List[Dict[str, str]]
    language: str
    difficulty: int = 1


@dataclass
class QuizResult:
    """Quiz result."""
    correct: bool
    user_answer: str
    correct_answer: str
    time_taken: float


@dataclass
class Progress:
    """Learning progress."""
    total_words: int = 0
    learned_words: int = 0
    mastered_words: int = 0
    streak_days: int = 0
    total_reviews: int = 0
    correct_reviews: int = 0
    minutes_practiced: int = 0
    level: str = "Beginner"


@dataclass
class LanguageProfile:
    """User's language learning profile."""
    language: str
    native_language: str = "English"
    level: str = "Beginner"
    goal: str = "Conversational"
    daily_goal: int = 20
    streak: int = 0
    last_practice: str = ""
    joined: str = ""


class VocabularyManager:
    """Manage vocabulary with spaced repetition (SM-2 algorithm)."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize vocabulary manager."""
        self.config = config or Config.get_instance()
        self.words_dir = self.config.config_dir / "vocabulary"
        self.words_dir.mkdir(parents=True, exist_ok=True)
        self._words: Dict[str, Word] = {}
        self._load_words()

    def _load_words(self) -> None:
        """Load vocabulary from disk."""
        for lang_file in self.words_dir.glob("*.json"):
            try:
                data = json.loads(lang_file.read_text())
                for word_id, word_data in data.items():
                    self._words[f"{word_data['language']}:{word_id}"] = Word(**word_data)
            except Exception as e:
                logger.debug(f"Failed to load {lang_file}: {e}")

    def _save_words(self) -> None:
        """Save vocabulary to disk."""
        by_language: Dict[str, Dict] = {}

        for key, word in self._words.items():
            lang = word.language
            if lang not in by_language:
                by_language[lang] = {}
            by_language[lang][word.id] = asdict(word)

        for lang, words in by_language.items():
            file_path = self.words_dir / f"{lang}.json"
            file_path.write_text(json.dumps(words, indent=2))

    def add_word(
        self,
        word: str,
        translation: str,
        language: str,
        **kwargs
    ) -> Word:
        """Add a new word."""
        word_id = hashlib.md5(f"{word}{language}".encode()).hexdigest()[:8]
        now = datetime.now().isoformat()

        vocab_word = Word(
            id=word_id,
            word=word,
            translation=translation,
            language=language,
            romanization=kwargs.get("romanization", ""),
            part_of_speech=kwargs.get("part_of_speech", ""),
            pronunciation=kwargs.get("pronunciation", ""),
            example_sentence=kwargs.get("example_sentence", ""),
            example_translation=kwargs.get("example_translation", ""),
            difficulty=kwargs.get("difficulty", 1),
            tags=kwargs.get("tags", []),
            learned=False,
            times_seen=0,
            times_correct=0,
            last_seen=now,
            next_review=now,
        )

        self._words[f"{language}:{word_id}"] = vocab_word
        self._save_words()

        return vocab_word

    def get_words_for_review(self, language: str, limit: int = 20) -> List[Word]:
        """Get words due for review."""
        now = datetime.now().isoformat()
        due_words = []

        for key, word in self._words.items():
            if word.language != language:
                continue
            if word.next_review <= now and not word.learned:
                due_words.append(word)

        due_words.sort(key=lambda w: w.next_review)
        return due_words[:limit]

    def review_word(
        self,
        word_id: str,
        language: str,
        quality: int
    ) -> Tuple[bool, float]:
        """Review a word using SM-2 algorithm.

        quality: 0-5 (0=complete blackout, 5=perfect recall)
        Returns: (correct, new_interval)
        """
        key = f"{language}:{word_id}"
        if key not in self._words:
            return False, 0

        word = self._words[key]
        word.times_seen += 1

        if quality >= 3:
            word.times_correct += 1
            correct = True
        else:
            correct = False
            word.ease_factor = max(1.3, word.ease_factor - 0.2)

        if quality < 3:
            word.interval = 1
        elif word.interval == 1:
            word.interval = 1
        elif word.interval == 2:
            word.interval = 6
        else:
            word.interval = int(word.interval * word.ease_factor)

        if word.times_correct >= 5 and word.ease_factor >= 2.5:
            word.learned = True
            word.interval = max(word.interval, 21)

        next_date = datetime.now() + timedelta(days=word.interval)
        word.next_review = next_date.isoformat()
        word.last_seen = datetime.now().isoformat()

        self._save_words()

        return correct, word.interval

    def get_stats(self, language: str) -> Dict[str, int]:
        """Get vocabulary statistics."""
        total = 0
        learned = 0
        mastered = 0
        due = 0

        now = datetime.now().isoformat()
        for word in self._words.values():
            if word.language == language:
                total += 1
                if word.learned:
                    learned += 1
                if word.times_correct >= 8:
                    mastered += 1
                if word.next_review <= now:
                    due += 1

        return {
            "total": total,
            "learned": learned,
            "mastered": mastered,
            "due": due,
            "progress": f"{(learned/total*100):.0f}%" if total > 0 else "0%"
        }


class LanguageTutor:
    """AI-powered language tutor."""

    LANGUAGES = {
        "spanish": {"name": "Spanish", "code": "es", "flag": "🇪🇸"},
        "french": {"name": "French", "code": "fr", "flag": "🇫🇷"},
        "german": {"name": "German", "code": "de", "flag": "🇩🇪"},
        "italian": {"name": "Italian", "code": "it", "flag": "🇮🇹"},
        "portuguese": {"name": "Portuguese", "code": "pt", "flag": "🇵🇹"},
        "japanese": {"name": "Japanese", "code": "ja", "flag": "🇯🇵"},
        "chinese": {"name": "Mandarin Chinese", "code": "zh", "flag": "🇨🇳"},
        "korean": {"name": "Korean", "code": "ko", "flag": "🇰🇷"},
        "russian": {"name": "Russian", "code": "ru", "flag": "🇷🇺"},
        "arabic": {"name": "Arabic", "code": "ar", "flag": "🇸🇦"},
        "hindi": {"name": "Hindi", "code": "hi", "flag": "🇮🇳"},
    }

    def __init__(
        self,
        config: Optional[Config] = None,
        llm: Optional["LLMBackend"] = None
    ):
        """Initialize language tutor."""
        self.config = config or Config.get_instance()
        self.llm = llm
        self.vocab = VocabularyManager(config)
        self.profiles_dir = self.config.config_dir / "language_profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._profiles: Dict[str, LanguageProfile] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load language profiles."""
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                data = json.loads(profile_file.read_text())
                self._profiles[profile_file.stem] = LanguageProfile(**data)
            except Exception:
                pass

    def _save_profile(self, language: str) -> None:
        """Save language profile."""
        if language in self._profiles:
            file_path = self.profiles_dir / f"{language}.json"
            file_path.write_text(json.dumps(asdict(self._profiles[language]), indent=2))

    def create_profile(
        self,
        language: str,
        native_language: str = "English",
        level: str = "Beginner",
        goal: str = "Conversational"
    ) -> LanguageProfile:
        """Create a new language learning profile."""
        profile = LanguageProfile(
            language=language,
            native_language=native_language,
            level=level,
            goal=goal,
            joined=datetime.now().isoformat()
        )

        self._profiles[language] = profile
        self._save_profile(language)

        return profile

    async def teach_vocabulary(
        self,
        language: str,
        topic: str
    ) -> List[Word]:
        """Teach vocabulary for a topic."""
        prompt = f"""Create a vocabulary list for {language} learners about "{topic}".
Return JSON array with this structure for 10 words:
[
  {{
    "word": "the word in {language}",
    "translation": "english translation",
    "romanization": "pronunciation guide (if applicable)",
    "part_of_speech": "noun/verb/adjective/etc",
    "example_sentence": "example in {language}",
    "example_translation": "english translation of example",
    "difficulty": 1-5 (1=easy, 5=hard)"
  }}
]"""

        messages = [
            {"role": "system", "content": f"You are a {language} language teacher."},
            {"role": "user", "content": prompt}
        ]

        result = await self.llm.async_chat(messages)

        try:
            words_data = json.loads(result)
            added_words = []

            for w in words_data:
                word = self.vocab.add_word(
                    word=w["word"],
                    translation=w["translation"],
                    language=language,
                    romanization=w.get("romanization", ""),
                    part_of_speech=w.get("part_of_speech", ""),
                    example_sentence=w.get("example_sentence", ""),
                    example_translation=w.get("example_translation", ""),
                    difficulty=w.get("difficulty", 1),
                    tags=[topic]
                )
                added_words.append(word)

            return added_words

        except Exception as e:
            logger.error(f"Failed to parse vocabulary: {e}")
            return []

    async def generate_grammar_explanation(
        self,
        language: str,
        topic: str
    ) -> str:
        """Generate grammar explanation."""
        prompt = f"""Explain {topic} grammar in {language} for beginners.
Include:
1. Basic rule explanation
2. 3 example sentences with translations
3. Common mistakes to avoid
4. Practice tips

Format as clear, educational content."""

        messages = [
            {"role": "system", "content": f"You are a {language} grammar expert."},
            {"role": "user", "content": prompt}
        ]

        return await self.llm.async_chat(messages)

    async def practice_conversation(
        self,
        language: str,
        scenario: str,
        user_message: str
    ) -> str:
        """Practice conversation."""
        prompt = f"""You are a friendly native {language} speaker helping someone practice.
Scenario: {scenario}

Respond naturally to help them practice {language}.
Be encouraging but also correct gently when appropriate.
Keep responses moderate in length.
If they make mistakes, subtly show the correct way without being harsh."""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ]

        return await self.llm.async_chat(messages)

    async def translate(
        self,
        text: str,
        from_lang: str,
        to_lang: str = "English"
    ) -> str:
        """Translate text."""
        prompt = f"""Translate the following {from_lang} text to {to_lang}.
If there are multiple possible translations, provide the most common one.
Only provide the translation, no explanations.

Text: {text}"""

        messages = [
            {"role": "system", "content": "You are a translator."},
            {"role": "user", "content": prompt}
        ]

        return await self.llm.async_chat(messages)

    async def correct_text(
        self,
        text: str,
        language: str,
        show_corrections: bool = True
    ) -> Dict[str, str]:
        """Correct text and provide feedback."""
        prompt = f"""Review this {language} text for errors.
{'- If there are errors, respond with: CORRECTED: [corrected text]\n  ERRORS: [list of errors with corrections]\n  EXPLANATIONS: [brief explanations of corrections]'
- If no errors, just say: NO ERRORS

Text: {text}"""

        messages = [
            {"role": "system", "content": f"You are a {language} language teacher."},
            {"role": "user", "content": prompt}
        ]

        result = await self.llm.async_chat(messages)

        return {
            "original": text,
            "correction": result if "NO ERRORS" not in result else text,
            "feedback": result
        }

    def generate_quiz(
        self,
        language: str,
        num_questions: int = 10,
        quiz_type: str = "mixed"
    ) -> List[Dict[str, Any]]:
        """Generate a quiz."""
        words = self.vocab.get_words_for_review(language, num_questions)

        if not words:
            return []

        quiz = []

        for word in words:
            if quiz_type == "multiple_choice":
                options = [word.translation]
                other_words = [w for w in self._words.values() if w.language == language and w.id != word.id]
                random.shuffle(other_words)
                for other in other_words[:3]:
                    options.append(other.translation)
                random.shuffle(options)

                quiz.append({
                    "type": "multiple_choice",
                    "question": f"What does '{word.word}' mean?",
                    "options": options,
                    "correct": word.translation,
                    "word_id": word.id,
                })

            elif quiz_type == "translation":
                quiz.append({
                    "type": "translation",
                    "question": f"Translate to {language}: {word.translation}",
                    "answer": word.word,
                    "word_id": word.id,
                })

            elif quiz_type == "fill_blank":
                if word.example_sentence:
                    sentence = word.example_sentence.replace(word.word, "_____")
                    quiz.append({
                        "type": "fill_blank",
                        "question": f"Fill in the blank: {sentence}",
                        "answer": word.word,
                        "hint": word.translation,
                        "word_id": word.id,
                    })

        random.shuffle(quiz)
        return quiz[:num_questions]

    def check_answer(
        self,
        language: str,
        word_id: str,
        answer: str,
        quality: int = 3
    ) -> Tuple[bool, int]:
        """Check answer and update spaced repetition."""
        return self.vocab.review_word(word_id, language, quality)


class LanguageLearner:
    """Complete language learning system."""

    def __init__(
        self,
        config: Optional[Config] = None,
        llm: Optional["LLMBackend"] = None
    ):
        """Initialize language learner."""
        self.config = config or Config.get_instance()
        self.llm = llm
        self.tutor = LanguageTutor(config, llm)
        self.vocab = VocabularyManager(config)

    async def start_lesson(
        self,
        language: str,
        topic: str
    ) -> Dict[str, Any]:
        """Start a lesson on a topic."""
        words = await self.tutor.teach_vocabulary(language, topic)

        grammar = await self.tutor.generate_grammar_explanation(language, topic)

        return {
            "language": language,
            "topic": topic,
            "words_learned": len(words),
            "grammar_explanation": grammar,
            "vocabulary": [asdict(w) for w in words],
        }

    async def practice(
        self,
        language: str,
        input_type: str,
        user_input: str
    ) -> Dict[str, Any]:
        """Practice with different input types."""
        if input_type == "translate":
            translation = await self.tutor.translate(
                user_input, language, "English"
            )
            return {
                "type": "translate",
                "input": user_input,
                "output": translation,
            }

        elif input_type == "speak":
            response = await self.tutor.practice_conversation(
                language, "Casual conversation", user_input
            )
            return {
                "type": "speak",
                "input": user_input,
                "output": response,
            }

        elif input_type == "correct":
            result = await self.tutor.correct_text(user_input, language)
            return {
                "type": "correct",
                "original": result["original"],
                "corrected": result["correction"],
                "feedback": result["feedback"],
            }

        return {}

    def get_dashboard(self, language: str) -> Dict[str, Any]:
        """Get learning dashboard."""
        stats = self.vocab.get_stats(language)

        profile = self.tutor._profiles.get(language)

        words_due = self.vocab.get_words_for_review(language, 5)
        review_words = [asdict(w) for w in words_due]

        return {
            "language": language,
            "level": profile.level if profile else "Beginner",
            "goal": profile.goal if profile else "Conversational",
            "streak": profile.streak if profile else 0,
            "statistics": stats,
            "words_due": review_words,
            "languages_available": list(LanguageTutor.LANGUAGES.keys()),
        }