# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary utilities
RUN apt-get update && apt-get install -y \
    iputils-ping \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Copy the cron job file to the cron.d directory
COPY cronjob /etc/cron.d/ha-monitoring-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/ha-monitoring-cron

# Apply the cron job
RUN crontab /etc/cron.d/ha-monitoring-cron

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir python-telegram-bot

RUN chmod +x /app/run_with_env.sh

# Make the script executable
RUN chmod +x /app/run.py

# Run the cron service in the foreground
CMD ["cron", "-f"]