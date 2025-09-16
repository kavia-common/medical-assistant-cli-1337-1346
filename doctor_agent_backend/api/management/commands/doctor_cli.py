import re
import json
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand, CommandParser


# PUBLIC_INTERFACE
def get_common_health_issue_medicines() -> Dict[str, List[str]]:
    """Return a mapping of common health issues to typical over-the-counter medicine suggestions.

    Notes:
    - This mapping serves as a simple rule-based 'tool' for the CLI agent.
    - It is NOT medical advice. Users should consult a healthcare provider.
    """
    return {
        # Head-related
        "headache": [
            "Acetaminophen (e.g., Tylenol)",
            "Ibuprofen (e.g., Advil, Motrin)",
            "Naproxen (e.g., Aleve)",
            "Aspirin (avoid in children/teens recovering from viral illness)",
        ],
        "migraine": [
            "Acetaminophen",
            "Ibuprofen",
            "Naproxen",
            "Combination analgesics (check labels: caffeine + acetaminophen/aspirin)",
        ],
        # Fever/Cold/Cough
        "fever": [
            "Acetaminophen",
            "Ibuprofen",
            "Hydration and rest",
        ],
        "cold": [
            "Decongestants (e.g., pseudoephedrine or phenylephrine; check contraindications)",
            "Antihistamines (e.g., loratadine, cetirizine, diphenhydramine)",
            "Cough suppressants (e.g., dextromethorphan)",
            "Expectorants (e.g., guaifenesin)",
            "Saline nasal sprays",
        ],
        "cough": [
            "Dextromethorphan (cough suppressant)",
            "Guaifenesin (expectorant)",
            "Honey (not for children under 1 year)",
            "Throat lozenges",
        ],
        "sore throat": [
            "Throat lozenges (e.g., menthol)",
            "Acetaminophen or Ibuprofen for pain",
            "Salt-water gargles",
        ],
        "congestion": [
            "Decongestants (e.g., pseudoephedrine or phenylephrine; check contraindications)",
            "Saline nasal sprays",
            "Topical nasal decongestant (short-term only, avoid rebound congestion)",
        ],
        # GI
        "stomachache": [
            "Bismuth subsalicylate (e.g., Pepto-Bismol)",
            "Antacids (e.g., calcium carbonate)",
            "Simethicone (for gas)",
            "Oral rehydration solutions if diarrhea",
        ],
        "nausea": [
            "Ginger products",
            "Bismuth subsalicylate (check contraindications)",
            "Oral rehydration solutions if vomiting",
        ],
        "diarrhea": [
            "Oral rehydration solutions",
            "Loperamide (when appropriate; avoid if fever/bloody stools unless advised)",
            "Bismuth subsalicylate",
        ],
        "constipation": [
            "Fiber supplements (e.g., psyllium)",
            "Osmotic laxatives (e.g., polyethylene glycol)",
            "Stool softeners (e.g., docusate)",
        ],
        "heartburn": [
            "Antacids (e.g., calcium carbonate)",
            "H2 blockers (e.g., famotidine)",
            "Proton pump inhibitors (short-term if appropriate; e.g., omeprazole)",
        ],
        # Musculoskeletal
        "back pain": [
            "Acetaminophen",
            "Ibuprofen or Naproxen (if appropriate)",
            "Topical analgesics (e.g., menthol, diclofenac gel)",
        ],
        "muscle pain": [
            "Acetaminophen",
            "Ibuprofen or Naproxen (if appropriate)",
            "Topical analgesics (e.g., menthol, diclofenac gel)",
        ],
        # Allergy
        "allergies": [
            "Antihistamines (e.g., cetirizine, loratadine, fexofenadine)",
            "Intranasal corticosteroids (e.g., fluticasone)",
            "Saline nasal rinses",
        ],
        # Skin
        "rash": [
            "Hydrocortisone 1% cream (mild inflammatory rashes)",
            "Oral antihistamines for itch (e.g., cetirizine)",
            "Calamine lotion",
        ],
        "sunburn": [
            "Aloe vera gel (cooling relief)",
            "NSAIDs for pain/inflammation (if appropriate)",
            "Cool compresses and hydration",
        ],
        # Others
        "earache": [
            "Acetaminophen",
            "Ibuprofen (if appropriate)",
            "Warm compresses",
        ],
        "toothache": [
            "Acetaminophen",
            "Ibuprofen (if appropriate)",
            "Topical oral anesthetics (e.g., benzocaine; follow label directions)",
        ],
        "insomnia": [
            "Diphenhydramine (short-term; note sedation and next-day drowsiness)",
            "Melatonin (consider sleep hygiene first)",
        ],
    }


def _normalize_text(text: str) -> str:
    """Normalize text for simple matching."""
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def _match_issue_to_key(user_text: str, issue_map: Dict[str, List[str]]) -> Optional[str]:
    """Try to match a user's text to a known health issue key."""
    normalized = _normalize_text(user_text)
    # Direct key match
    for key in issue_map.keys():
        if key in normalized:
            return key
    # Token overlap heuristic
    user_tokens = set(normalized.split())
    best_key = None
    best_overlap = 0
    for key in issue_map.keys():
        key_tokens = set(key.split())
        overlap = len(user_tokens & key_tokens)
        if overlap > best_overlap and overlap > 0:
            best_overlap = overlap
            best_key = key
    return best_key


class SimpleConversationalMemory:
    """A minimal in-memory conversation store to mimic conversational memory."""

    def __init__(self, k: int = 5):
        self.k = k
        self.messages: List[Dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        # keep only last k messages
        if len(self.messages) > self.k:
            self.messages = self.messages[-self.k :]

    def context(self) -> str:
        """Return a serialized context string of the recent conversation."""
        return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in self.messages)


def _format_medicine_response(issue_key: str, meds: List[str]) -> str:
    bullet_list = "\n".join(f"- {m}" for m in meds)
    disclaimer = (
        "Important: Over-the-counter options may not be appropriate for everyone. "
        "Consult a healthcare provider before taking any medication. "
        "Read labels carefully, check for allergies, contraindications, "
        "and potential interactions. If symptoms are severe, persistent, or worsening, seek medical care."
    )
    return (
        f"For {issue_key}, typical over-the-counter options include:\n"
        f"{bullet_list}\n\n{disclaimer}"
    )


def _fallback_llm_like_response(user_text: str, context: str) -> str:
    """A placeholder LLM-like response to keep the CLI self-contained without external API calls.

    In the full system, this is where you'd integrate LangChain with a real LLM.
    """
    # Keep it simple and safe.
    return (
        "I understand. To help you better, can you share more details (onset, severity, relevant medical history)? "
        "Note: I am not a substitute for professional medical advice. If you experience severe or persistent symptoms, seek care."
    )


class Command(BaseCommand):
    """Django management command to run the doctor assistant CLI with OTC suggestion tool."""

    help = (
        "Run a simple doctor assistant CLI with conversational memory and a rule-based OTC medicine suggester."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        # PUBLIC_INTERFACE
        parser.add_argument(
            "--issue",
            type=str,
            required=False,
            help="Optional: Ask directly about a common health issue (e.g., 'headache'). If provided, the CLI will output suggestions once and exit.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output response as JSON (useful for programmatic use).",
        )

    def handle(self, *args, **options) -> None:
        """Entry point for the CLI loop."""
        issue_map = get_common_health_issue_medicines()
        memory = SimpleConversationalMemory(k=8)

        # Single-shot mode via --issue
        direct_issue: Optional[str] = options.get("issue")
        as_json: bool = options.get("json", False)
        if direct_issue:
            key = _match_issue_to_key(direct_issue, issue_map)
            if key:
                resp = _format_medicine_response(key, issue_map[key])
            else:
                resp = (
                    "I couldn't match that to a common health issue. "
                    "You can try asking about: "
                    + ", ".join(sorted(issue_map.keys()))
                    + ". "
                    "Consult a healthcare provider before taking any medication."
                )
            if as_json:
                self.stdout.write(json.dumps({"input": direct_issue, "response": resp}))
            else:
                self.stdout.write(resp)
            return

        # Interactive mode
        self.stdout.write("Doctor Assistant CLI")
        self.stdout.write("Type 'exit' to quit.")
        self.stdout.write("Ask about common health issues (e.g., 'What for headache?').\n")

        while True:
            try:
                user_text = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                self.stdout.write("\nExiting...")
                break

            if user_text.lower() in {"exit", "quit"}:
                self.stdout.write("Goodbye.")
                break

            if not user_text:
                continue

            memory.add("user", user_text)

            # Check for an identifiable common issue and reply with OTC suggestions
            matched_key = _match_issue_to_key(user_text, issue_map)
            if matched_key:
                response = _format_medicine_response(matched_key, issue_map[matched_key])
                memory.add("assistant", response)
                self.stdout.write(f"\n{response}\n")
                continue

            # Otherwise, produce a safe general response (placeholder for LLM integration)
            context = memory.context()
            response = _fallback_llm_like_response(user_text, context)
            memory.add("assistant", response)
            self.stdout.write(f"\n{response}\n")
