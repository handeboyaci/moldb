
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Create a virtual environment
RUN apt-get update && apt-get install -y git

# Install Razi directly from GitHub
RUN pip install git+https://github.com/rvianello/razi.git

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . .

ENV PYTHONPATH=/app

# Run uvicorn when the container launches
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
