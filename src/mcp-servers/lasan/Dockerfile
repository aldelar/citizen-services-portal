FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server_ladwp.py .
COPY src/ ./src/

EXPOSE 8000
CMD ["python", "mcp_server_ladwp.py"]
