FROM python:3.12-slim

WORKDIR /app

# Build context is repo root (set in azure.yaml), so copy agent folder explicitly
COPY src/agents/csp-agent/ /app/user_agent/
WORKDIR /app/user_agent

RUN if [ -f requirements.txt ]; then \
        pip install -r requirements.txt; \
    else \
        echo "No requirements.txt found"; \
    fi

EXPOSE 8088

CMD ["python", "main.py"]
