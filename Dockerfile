# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Copy the temp files into the container
COPY temp/.env.docker .env
COPY temp/mounts.json mounts.json

# Run run.py
CMD ["python", "run.py"]