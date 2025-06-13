# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code
COPY . .

# Run gunicorn when the container launches. Fly.io automatically sets the PORT env var.
CMD ["gunicorn", "name_analysis_api:app", "--bind", "0.0.0.0:$PORT", "--workers", "1"]
