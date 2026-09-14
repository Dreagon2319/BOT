FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium and all required Linux dependencies
RUN playwright install --with-deps chromium

# Copy application
COPY main.py .

# Railway provides the actual PORT environment variable.
# The application itself reads it from os.environ.
CMD ["python", "main.py"]
