# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install postgresql-client for database utilities
RUN apt-get update && apt-get install -y git postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt .
COPY requirements-dev.txt .
COPY requirements-test.txt .

# Install production dependencies
RUN pip install -r requirements.txt

# Install development and testing dependencies based on build argument
ARG BUILD_ENV
RUN if [ "$BUILD_ENV" = "dev" ]; then pip install -r requirements-dev.txt; pip install -r requirements-test.txt; fi

# Copy the rest of the application's code into the container at /app
COPY . .

ENV PYTHONPATH=/app

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Use the entrypoint script to start the application
ENTRYPOINT ["/app/entrypoint.sh"]
