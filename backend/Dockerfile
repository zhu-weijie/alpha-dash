# backend/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files to disk
# and to prevent buffering of stdout and stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies if any (e.g., for psycopg2 if not using -binary, but -binary includes them)
# RUN apt-get update && apt-get install -y ... && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port the app runs on (Uvicorn default is 8000)
EXPOSE 8000

# Command to run the application
# For development with auto-reload:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# For production, you might remove --reload:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]