# medical-assistant-cli-1337-1346

This workspace contains a Django backend that exposes a console-based Doctor Agent CLI using LangChain and OpenAI.

Quick start:
1) Install Python dependencies:
   - cd medical-assistant-cli-1337-1346/doctor_agent_backend
   - pip install -r requirements.txt

2) Set environment variables (do not commit secrets):
   - export OPENAI_API_KEY=sk-...
   - export OPENAI_MODEL=gpt-4o-mini   # optional

3) Run migrations (standard Django step, even if unused here):
   - python manage.py migrate

4) Launch the CLI:
   - python manage.py doctor_agent
   - Options:
     * --model gpt-4o-mini
     * --no-color
     * --system-prompt "You are a helpful clinical assistant."

In-CLI commands:
- Type your question and press Enter.
- /triage <text> -> calls a basic triage tool returning JSON advice (non-diagnostic).
- /reset -> clears conversational memory.
- /exit -> quits.

Notes:
- This is a rapid prototype for educational/demo purposes. It is not a medical device, and not validated for clinical use. Do not use for patient care.