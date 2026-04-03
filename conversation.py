"""
conversation.py
Core state machine for the TalentScout Hiring Assistant.
Manages conversation stages, LLM API calls, and candidate data extraction.
"""

import json
import os
import re
import anthropic
from prompts import STAGE_INSTRUCTIONS, SYSTEM_PROMPT
from data_handler import (
    extract_email_from_text,
    extract_years_from_text,
    validate_email,
    validate_phone,
    save_candidate,
    format_candidate_summary,
)


# Conversation stages in order
STAGES = [
    "greeting",
    "collect_name",
    "collect_email",
    "collect_phone",
    "collect_location",
    "collect_experience",
    "collect_position",
    "collect_techstack",
    "technical_questions",
    "wrap_up",
    "ended",
]

EXIT_KEYWORDS = {"bye", "goodbye", "quit", "exit", "done", "that's all", "thats all", "stop"}

# How many technical questions to ask
NUM_TECH_QUESTIONS = 5


class ConversationManager:
    """
    Manages the full lifecycle of a candidate screening conversation.

    Attributes:
        stage (str): Current conversation stage.
        history (list): Full chat history for context window.
        candidate (dict): Collected candidate information.
        questions (list): Generated technical questions.
        q_index (int): Index of current question being asked.
    """

    def __init__(self):
        self.stage = "greeting"
        self.history = []
        self.candidate = {}
        self.questions = []
        self.q_index = 0
        from llm_provider import LLMProvider
        self.llm = LLMProvider()

    # ── Public interface ───────────────────────────────────────────────────────

    def get_greeting(self) -> str:
        """Generate and return the opening greeting message."""
        response = self._call_llm("greeting")
        self._advance_stage()  # move to collect_name
        return response

    def process(self, user_input: str) -> str:
        """
        Process a user message and return the assistant's response.

        Args:
            user_input: Raw text from the candidate.

        Returns:
            Assistant response string.
        """
        if len(user_input.strip()) < 2:
            return "Could you please provide a bit more detail?"

        # Append user message to history
        self.history.append({"role": "user", "content": user_input})

        # Check for exit intent
        if self._is_exit(user_input):
            self.stage = "ended"
            response = self._farewell()
            self.history.append({"role": "assistant", "content": response})
            return response

        # If already ended, just acknowledge
        if self.stage == "ended":
            response = "It was great speaking with you! Your application is in good hands. 👋"
            self.history.append({"role": "assistant", "content": response})
            return response

        # Extract structured data from input before calling LLM
        self._extract_data(user_input)

        # Route to the right handler
        response = self._route()

        self.history.append({"role": "assistant", "content": response})
        return response

    @property
    def is_ended(self) -> bool:
        return self.stage == "ended"

    @property
    def progress_pct(self) -> int:
        """Return 0-100 progress through the conversation."""
        idx = STAGES.index(self.stage) if self.stage in STAGES else 0
        return int((idx / (len(STAGES) - 1)) * 100)

    @property
    def stage_label(self) -> str:
        labels = {
            "greeting": "Welcome",
            "collect_name": "Your Name",
            "collect_email": "Contact Info",
            "collect_phone": "Contact Info",
            "collect_location": "Location",
            "collect_experience": "Experience",
            "collect_position": "Desired Role",
            "collect_techstack": "Tech Stack",
            "technical_questions": f"Technical Q&A ({self.q_index}/{len(self.questions) or NUM_TECH_QUESTIONS})",
            "wrap_up": "Wrap Up",
            "ended": "Complete ✓",
        }
        return labels.get(self.stage, self.stage)

    # ── Routing ────────────────────────────────────────────────────────────────

    def _route(self) -> str:
        """Route to the correct stage handler and manage transitions."""

        if self.stage in (
            "collect_name", "collect_email", "collect_phone",
            "collect_location", "collect_experience",
            "collect_position", "collect_techstack",
        ):
            response = self._call_llm(self.stage)
            # Validate before advancing
            if self._can_advance():
                self._advance_stage()
                # If we just finished collecting tech stack, generate questions
                if self.stage == "technical_questions":
                    self._generate_questions()
            return response

        elif self.stage == "technical_questions":
            return self._handle_tech_questions()

        elif self.stage == "wrap_up":
            return self._handle_wrap_up()

        else:
            return self._call_llm(self.stage)

    # ── Stage handlers ─────────────────────────────────────────────────────────

    def _handle_tech_questions(self) -> str:
        """Ask the next technical question, or transition to wrap-up."""
        if not self.questions:
            self._generate_questions()

        extra = {
            "tech_stack": self.candidate.get("tech_stack", ""),
            "questions_asked": str(self.questions[: self.q_index]),
            "q_num": self.q_index + 1,
            "q_total": len(self.questions),
        }

        # If we've asked all questions, move to wrap-up
        if self.q_index >= len(self.questions):
            self.stage = "wrap_up"
            return self._handle_wrap_up()

        # Inject the specific question into context so the LLM knows what to ask
        question_hint = f"\n\nASK THIS EXACT QUESTION NOW (word it naturally):\n{self.questions[self.q_index]}"
        extra_with_q = {**extra}

        response = self._call_llm("technical_questions", extra=extra_with_q, suffix=question_hint)
        self.q_index += 1
        return response

    def _handle_wrap_up(self) -> str:
        """Generate the closing message, save candidate data."""
        summary = format_candidate_summary(self.candidate)
        response = self._call_llm(
            "wrap_up",
            extra={"candidate_summary": summary},
        )
        # Persist data
        self.candidate["questions_asked"] = self.questions
        self.candidate["session_summary"] = summary
        try:
            save_candidate(self.candidate)
        except Exception:
            pass  # Don't crash if saving fails
        self.stage = "ended"
        return response

    # ── LLM interface ──────────────────────────────────────────────────────────

    def _call_llm(self, stage: str, extra: dict = None, suffix: str = "") -> str:
        """
        Call the Claude API for the given stage.

        Args:
            stage: Stage key to pull instructions for.
            extra: Format variables for the stage instruction template.
            suffix: Extra text appended to the system instruction (for question injection).

        Returns:
            The assistant's text response.
        """
        instruction = STAGE_INSTRUCTIONS.get(stage, "")
        if extra:
            try:
                instruction = instruction.format(**extra)
            except KeyError:
                pass
        instruction += suffix

        system = SYSTEM_PROMPT + "\n\nCURRENT TASK:\n" + instruction

        # Keep history window manageable (last 20 messages)
        trimmed_history = self.history[-20:]

        for _ in range(3):
            try:
                return self.llm.generate(system, trimmed_history)
            except Exception:
                continue

        return "Sorry, I'm having trouble responding right now. Please try again."

    def _generate_questions(self):
        """Call LLM to generate a list of technical questions for the candidate's stack."""
        tech_stack = self.candidate.get("tech_stack", ["Python"])
        if isinstance(tech_stack, list):
            tech_stack_text = ", ".join(tech_stack)
        else:
            tech_stack_text = str(tech_stack)

        experience = self.candidate.get("experience", "0")
        try:
            exp_num = float(re.search(r"\d+(\.\d+)?", experience).group())
        except Exception:
            exp_num = 0

        difficulty = "advanced" if exp_num >= 3 else "basic"
        instruction = STAGE_INSTRUCTIONS["generate_questions"].format(
            n=NUM_TECH_QUESTIONS,
            tech_stack=tech_stack_text,
        ) + f"\nDifficulty level: {difficulty}"
        system = SYSTEM_PROMPT + "\n\nCURRENT TASK:\n" + instruction

        raw = ""
        for _ in range(3):
            try:
                raw = self.llm.generate(system, [{"role": "user", "content": tech_stack}])
                break
            except Exception:
                continue

        try:
            self.questions = json.loads(raw)
        except Exception:
            self.questions = [
                q.strip()
                for q in raw.split("\n")
                if "?" in q
            ][:NUM_TECH_QUESTIONS]

        if not self.questions:
            self.questions = [
                f"Can you walk me through a challenging project where you used {tech_stack_text}?",
                f"What are the most important best practices you follow when working with {tech_stack_text}?",
                "How do you approach debugging a production issue you've never seen before?",
                "Describe your experience with version control and code review processes.",
                "What's a technical concept you've had to explain to a non-technical stakeholder?",
            ]

    # ── Data extraction ────────────────────────────────────────────────────────

    def _extract_data(self, text: str):
        """
        Heuristically extract structured data from free-form user input
        based on the current stage.
        """
        stage = self.stage
        text_clean = text.strip()

        if stage == "collect_name" and not self.candidate.get("name"):
            # Take the whole input as name if it's short
            if len(text_clean.split()) <= 5:
                self.candidate["name"] = text_clean.title()

        elif stage == "collect_email":
            email = extract_email_from_text(text_clean)
            if email:
                self.candidate["email"] = email

        elif stage == "collect_phone":
            self.candidate["phone"] = text_clean if text_clean.lower() not in ("skip", "no", "n/a", "-") else "Not provided"

        elif stage == "collect_location":
            self.candidate["location"] = text_clean

        elif stage == "collect_experience":
            self.candidate["experience"] = extract_years_from_text(text_clean)

        elif stage == "collect_position":
            self.candidate["desired_position"] = text_clean

        elif stage == "collect_techstack":
            self.candidate["tech_stack"] = [
                tech.strip() for tech in text_clean.split(",") if tech.strip()
            ]

    def _can_advance(self) -> bool:
        """
        Decide whether the current stage has enough data to advance.
        Returns True if we should move to the next stage.
        """
        stage = self.stage
        if stage == "collect_email":
            return validate_email(self.candidate.get("email", ""))
        if stage == "collect_phone":
            phone = self.candidate.get("phone", "")
            return phone == "Not provided" or validate_phone(phone)
        # All other stages: always advance after one response
        return True

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _advance_stage(self):
        """Move to the next stage in the pipeline."""
        idx = STAGES.index(self.stage)
        if idx < len(STAGES) - 1:
            self.stage = STAGES[idx + 1]

    def _is_exit(self, text: str) -> bool:
        """Check if the user wants to end the conversation."""
        lower = text.lower().strip()
        return any(kw in lower for kw in EXIT_KEYWORDS)

    def _farewell(self) -> str:
        """Return a graceful farewell message."""
        name = self.candidate.get("name", "")
        greeting = f" {name}," if name else ","
        return (
            f"Thank you{greeting} it was a pleasure speaking with you! 🎯\n\n"
            "Your responses have been recorded and the TalentScout team will be in touch "
            "within **3–5 business days**. We look forward to potentially working together!\n\n"
            "Best of luck, and take care! 👋"
        )
