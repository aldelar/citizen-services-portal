FROM python:3.12-slim

WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Environment variables
ENV NICEGUI_PORT=8080
ENV NICEGUI_HOST=0.0.0.0
ENV USE_MOCK_AUTH=true

# Run the application
CMD ["python", "main.py"]
