# Minimal Dockerfile for testing
FROM python:3.10-slim

WORKDIR /app

# Copy minimal requirements
COPY requirements-minimal.txt .

# Install only gradio
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy minimal app
COPY app_minimal.py .

# Expose port
EXPOSE 7860

# Run the app
CMD ["python", "app_minimal.py"]
