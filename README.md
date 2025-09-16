# medical-assistant-cli-1337-1346

Doctor Agent Backend (Django)
- Includes a management command implementing a simple conversational CLI with a rule-based OTC medicine suggestion tool.

How to run
1) Change directory into the Django project root:
   cd medical-assistant-cli-1337-1346/doctor_agent_backend

2) Run the CLI interactively:
   python manage.py doctor_cli

3) Ask about common health issues (examples):
   - "What can I take for a headache?"
   - "Any suggestions for fever?"
   - "Help with cough?"

4) Single-shot mode (useful for scripting):
   python manage.py doctor_cli --issue "headache"

5) JSON output:
   python manage.py doctor_cli --issue "stomachache" --json

Notes and safety
- This tool suggests typical over-the-counter options for common issues and is NOT medical advice.
- Always consult a healthcare provider before taking any medication.
- Read labels carefully and check for contraindications, allergies, and interactions.
