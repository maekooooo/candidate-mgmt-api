FROM python:3.12-slim-bullseye

# Set environment variables for security
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install only necessary system dependencies and clean up
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps **as root**, then switch to non‐root
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create/appuser and switch
RUN useradd -m appuser
USER appuser

# Copy app code
COPY --chown=appuser:appuser . .

# Expose & launch
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]