import os
import sys
import time
import json
import textwrap

from django.core.management.base import BaseCommand, CommandError

# Lazy import to avoid ImportError if dependencies are missing at Django load time
def _lazy_imports():
    try:
        from langchain_openai import ChatOpenAI
        from langchain.memory import ConversationBufferMemory
        from langchain.agents import initialize_agent, AgentType
        from langchain.tools import BaseTool
        return {
            "ChatOpenAI": ChatOpenAI,
            "ConversationBufferMemory": ConversationBufferMemory,
            "initialize_agent": initialize_agent,
            "AgentType": AgentType,
            "BaseTool": BaseTool,
        }
    except Exception as e:
        raise CommandError(
            "LangChain/OpenAI dependencies not found or failed to import. "
            "Please ensure requirements are installed. Original error: "
            f"{e}"
        )

# PUBLIC_INTERFACE
class Command(BaseCommand):
    """
    Django management command that runs a console-based LangChain agent
    for clinicians. It uses OpenAI's GPT models, includes conversational
    memory, and at least one basic medical tool.

    Usage:
      python manage.py doctor_agent
      python manage.py doctor_agent --model gpt-4o-mini
      python manage.py doctor_agent --no-color
      python manage.py doctor_agent --system-prompt "You are a helpful clinical assistant."

    Environment variables (must be set externally; do not commit secrets):
      - OPENAI_API_KEY: API key for OpenAI.
      - OPENAI_MODEL: Optional default model (e.g., gpt-4o-mini, gpt-4o, gpt-3.5-turbo).
    """

    help = "Run a console-based LangChain doctor agent with memory and tools."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            help="Model to use (default: env OPENAI_MODEL or gpt-4o-mini)."
        )
        parser.add_argument(
            "--no-color",
            action="store_true",
            help="Disable ANSI colors in console output."
        )
        parser.add_argument(
            "--system-prompt",
            type=str,
            default=(
                "You are a helpful clinical assistant for licensed clinicians. "
                "You provide succinct, evidence-informed suggestions and clearly "
                "state limitations. You are not a substitute for clinical judgment. "
                "Always ask clarifying questions if the input is ambiguous. "
                "When referencing data, prefer general, widely accepted clinical "
                "guidelines, and avoid providing personal health information."
            ),
            help="Override the default system prompt."
        )

    def handle(self, *args, **options):
        # Verify environment variable for OpenAI key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise CommandError(
                "OPENAI_API_KEY is not set. Please configure it in the environment. "
                "Do not hardcode secrets in code; set them via environment or .env."
            )

        imports = _lazy_imports()
        ChatOpenAI = imports["ChatOpenAI"]
        ConversationBufferMemory = imports["ConversationBufferMemory"]
        initialize_agent = imports["initialize_agent"]
        AgentType = imports["AgentType"]
        BaseTool = imports["BaseTool"]

        model_name = options["model"]
        use_color = not options["no_color"]
        system_prompt = options["system_prompt"]

        # Set up a basic medical tool
        class TriageTool(BaseTool):
            """
            A simple triage suggestion tool.
            Inputs: chief complaint text
            Output: non-diagnostic, general urgency suggestion.
            """

            name: str = "basic_triage_advice"
            description: str = (
                "Provide general triage-level advice for a given symptom summary. "
                "This is not a diagnosis. It suggests urgency levels like emergency, "
                "urgent, routine, or self-care based on common red flags."
            )

            # PUBLIC_INTERFACE
            def _run(self, query: str) -> str:
                """
                Synchronously provide heuristic triage advice.

                Args:
                    query: Chief complaint or symptom summary.

                Returns:
                    A string of general triage advice with clear disclaimers.
                """
                text = query.lower()

                emergency_flags = [
                    "chest pain", "shortness of breath", "severe headache",
                    "loss of consciousness", "uncontrolled bleeding", "stroke",
                    "weakness on one side", "sudden weakness", "severe abdominal pain"
                ]
                urgent_flags = [
                    "fever > 39", "high fever", "persistent vomiting", "dehydration",
                    "new confusion", "moderate abdominal pain", "worsening infection"
                ]

                # Extremely simple heuristic; purely for prototyping/demonstration
                if any(flag in text for flag in emergency_flags):
                    urgency = "Emergency care recommended"
                    guidance = (
                        "Based on common red flags, this may require immediate evaluation. "
                        "If in a clinical setting, consider urgent stabilization and "
                        "activation of emergency pathways."
                    )
                elif any(flag in text for flag in urgent_flags):
                    urgency = "Urgent evaluation recommended"
                    guidance = (
                        "Suggest timely in-person evaluation. Monitor vitals and consider "
                        "supportive care based on local protocols."
                    )
                else:
                    urgency = "Routine or self-care may be reasonable"
                    guidance = (
                        "If symptoms are mild and stable, routine follow-up or self-care "
                        "with safety-net instructions may be reasonable. Reassess if any "
                        "red flags emerge."
                    )

                disclaimer = (
                    "This is not medical advice or a diagnosis. Use clinical judgment "
                    "and local protocols. If unsure, escalate appropriately."
                )

                result = {
                    "input_summary": query.strip(),
                    "triage_urgency": urgency,
                    "guidance": guidance,
                    "disclaimer": disclaimer
                }
                return json.dumps(result, indent=2)

            async def _arun(self, query: str) -> str:
                # For simplicity in CLI, not implementing async path.
                raise NotImplementedError("Async not supported in this CLI tool.")

        tools = [TriageTool()]

        # Memory: Conversation buffer to maintain context during the session
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # LLM initialization (OpenAI chat model via langchain_openai)
        llm = ChatOpenAI(
            temperature=0.1,
            model=model_name,
            max_tokens=None,  # let API decide reasonable default
            # api_key is read from OPENAI_API_KEY env by the client library
        )

        # Initialize an agent with tools and conversational memory
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=False,
            max_iterations=6,
            memory=memory,
            handle_parsing_errors=True
        )

        # Greet the user and show quick instructions
        self._println(self._banner_text(), color=use_color, color_code="cyan")
        self._println("Rapid prototype for clinical use. Do not use for real patient care without validation.", color=use_color, color_code="yellow")
        self._println("Type your question. Use '/triage <text>' to directly call the triage tool.", color=use_color, color_code="yellow")
        self._println("Type '/reset' to clear memory, '/exit' to quit.", color=use_color, color_code="yellow")
        self._println(f"Model: {model_name}", color=use_color, color_code="magenta")
        self._println("------------------------------------------------------------", color=use_color, color_code="cyan")

        # Seed the conversation with the system prompt
        # We add it as a first turn for context; many ChatOpenAI wrappers support system messages,
        # but for portability here we simply share it in the first user input displayed to the model.
        seed_instruction = (
            "System prompt:\n" + system_prompt + "\n\n"
            "Acknowledge with a brief confirmation."
        )
        try:
            ack = agent.run(seed_instruction)
            self._println("\n[System acknowledged]:", color=use_color, color_code="green")
            self._println(self._wrap(ack), color=use_color)
        except Exception as e:
            self._println(f"Warning: Failed to seed system prompt: {e}", color=use_color, color_code="red")

        # Main REPL loop
        while True:
            try:
                user_input = input(self._colorize("\nYou> ", use_color, "blue"))
            except (EOFError, KeyboardInterrupt):
                self._println("\nExiting.", color=use_color, color_code="yellow")
                break

            if not user_input.strip():
                continue

            # Commands
            if user_input.strip().lower() in ["/exit", "exit", "quit", ":q"]:
                self._println("Goodbye!", color=use_color, color_code="yellow")
                break

            if user_input.strip().lower() in ["/reset", "reset"]:
                memory.clear()
                self._println("Conversation memory cleared.", color=use_color, color_code="yellow")
                continue

            if user_input.strip().startswith("/triage"):
                # Direct tool invocation
                query = user_input.strip()[7:].strip()
                if not query:
                    self._println("Usage: /triage <chief complaint or symptom summary>", color=use_color, color_code="yellow")
                    continue
                try:
                    tool_result = tools[0].run(query)
                    self._println("Triage tool result:", color=use_color, color_code="green")
                    self._println(self._wrap(tool_result), color=use_color)
                except Exception as e:
                    self._println(f"Tool error: {e}", color=use_color, color_code="red")
                continue

            # Normal agent interaction
            self._println("Agent thinking...", color=use_color, color_code="cyan")
            start = time.time()
            try:
                response = agent.run(user_input)
                elapsed = time.time() - start
                self._println(f"\nAgent ({elapsed:.1f}s):", color=use_color, color_code="green")
                self._println(self._wrap(response), color=use_color)
            except Exception as e:
                self._println(f"Agent error: {e}", color=use_color, color_code="red")

    # Helper printing utilities
    def _wrap(self, text: str, width: int = 100) -> str:
        try:
            return "\n".join(textwrap.fill(line, width=width) for line in text.splitlines())
        except Exception:
            return text

    def _colorize(self, text: str, use_color: bool, color: str) -> str:
        if not use_color:
            return text
        colors = {
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "reset": "\033[0m",
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"

    def _println(self, text: str, color: bool = True, color_code: str = "reset"):
        sys.stdout.write(self._colorize(text + "\n", color, color_code))
        sys.stdout.flush()

    def _banner_text(self) -> str:
        return (
            "Doctor Agent CLI (LangChain + OpenAI)\n"
            "For rapid prototyping / educational purposes only."
        )
