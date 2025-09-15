
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install postgresql-client for database utilities
RUN apt-get update && apt-get install -y git postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . .

ENV PYTHONPATH=/app
ENV SQLALCHEMY_DATABASE_URL="postgresql://user:password@db:5432/chemstructdb"

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Use the entrypoint script to start the application
ENTRYPOINT ["/app/entrypoint.sh"]
