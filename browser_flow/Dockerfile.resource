FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn python-dotenv

# Copy resource service
COPY resource_service.py .

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "resource_service:app", "--host", "0.0.0.0", "--port", "8001"]
