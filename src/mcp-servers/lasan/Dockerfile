FROM python:3.12-slim

WORKDIR /app

# Copy and install shared library first
COPY src/shared/ ./shared/
RUN pip install --no-cache-dir ./shared

# Copy and install LASAN MCP server
COPY src/mcp-servers/lasan/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/mcp-servers/lasan/mcp_server_lasan.py .
COPY src/mcp-servers/lasan/src/ ./src/

EXPOSE 8000
CMD ["python", "mcp_server_lasan.py"]
