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

# Create a script to save environment variables
RUN echo '#!/bin/bash\n\
printenv | grep "TELEGRAM" > /etc/environment\n\
cron -f' > /app/start.sh && \
chmod +x /app/start.sh

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir python-telegram-bot

# Set up crontab differently
RUN echo "* * * * * root . /etc/environment && /app/run_with_env.sh >> /var/log/cron_output.log 2>&1" > /etc/cron.d/ha-monitoring-cron \
    && chmod 0644 /etc/cron.d/ha-monitoring-cron \
    && crontab /etc/cron.d/ha-monitoring-cron

RUN chmod +x /app/run_with_env.sh
RUN chmod +x /app/run.py

# Create log file and set permissions
RUN touch /var/log/cron_output.log && chmod 0666 /var/log/cron_output.log

# Run the start script instead of cron directly
CMD ["/app/start.sh"]