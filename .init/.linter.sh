#!/bin/bash
cd /home/kavia/workspace/code-generation/medical-assistant-cli-1337-1346/doctor_agent_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

