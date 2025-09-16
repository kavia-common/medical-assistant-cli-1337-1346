# Doctor Agent CLI

A console-based clinical assistant prototype powered by LangChain and OpenAI.

Usage:
- Run: `python manage.py doctor_agent`
- Choose model: `python manage.py doctor_agent --model gpt-4o-mini`
- No ANSI colors: `python manage.py doctor_agent --no-color`
- Override system prompt: `python manage.py doctor_agent --system-prompt "You are a helpful assistant."`

Commands inside the REPL:
- Type your clinical question and press Enter.
- `/triage <text>`: Call the basic triage tool directly with a chief complaint or symptom summary.
- `/reset`: Clear conversation memory.
- `/exit`: Quit the agent.

Environment variables (set in deployment environment, do not commit):
- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (optional default model)

Notes:
- This is a rapid prototype, not a medical device. Do not use it for patient care without clinical validation and approvals.
