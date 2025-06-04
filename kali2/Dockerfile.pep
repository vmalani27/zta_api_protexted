FROM python:3.12-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY pep_service.py .

# Expose PEP service port
EXPOSE 5003

# Start PEP service
CMD ["uvicorn", "pep_service:app", "--host", "0.0.0.0", "--port", "5003"] 