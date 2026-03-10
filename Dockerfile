FROM python:3.11-slim

# 1. Install system dependencies FIRST (including git)
# This allows pip to install libraries directly from GitHub
RUN apt-get update && apt-get install -y \
    cron \
    git \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 2. Set up working directory
WORKDIR /app

# 3. Copy only the list of libraries
COPY requirements.txt .

# 4. Install project dependencies
# Now that 'git' is installed above, this will work!
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your project code
COPY . .

# 6. Set the path so Python finds the 'src' folder
ENV PYTHONPATH="/app"

# 7. Setup Cron
COPY crontab /etc/cron.d/sync-jobs
RUN chmod 0644 /etc/cron.d/sync-jobs && crontab /etc/cron.d/sync-jobs

# 8. Start the cron daemon
CMD ["cron", "-f"]