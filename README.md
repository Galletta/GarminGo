# 🚀 GarminGo: Make data-driven decisions about your health, fitness, and longevity! 📄📈

Pull your daily health metrics from Garmin Connect and save them directly to a user-friendly CSV file or Google Sheets.

I created this utility to feed my data into AI (e.g. LLMs like Claude, ChatGPT, and Gemini) so that I could gain insights for improving my health and longevity. Even if you aren't technical, getting your data as a CSV is pretty simple!

Once you have the files here, Python installed, and the project set up (step-by-step instructions below), you can run it by typing `garmingo`! While it's simple for non-technical users, it also supports power users, allowing you to schedule and run everything via command line arguments.

---

## Table of Contents
* [✨ Screenshots](#-screenshots)
* [🌟 Advanced Features (Added in this Fork)](#-advanced-features-added-in-this-fork)
* [🔄 The Ultimate Health Data Pipeline](#-the-ultimate-health-data-pipeline-omron---garmin---sheets)
* [🛠️ Technical Documentation: Sync Pipeline](#️-technical-documentation-sync-pipeline)
* [🚀 Quick Start: Get Your Data as a CSV File](#-quick-start-get-your-data-as-a-csv-file)
* [⚙️ Advanced Options & Google Sheets Integration](#️-advanced-options--google-sheets-integration)
* [📊 Available Metrics](#-available-metrics)
* [📖 Metric Dictionary & Data Sources](#-metric-dictionary--data-sources)
* [🛠️ Troubleshooting](#️-troubleshooting)
* [🔒 Security Notes](#-security-notes)
* [📜 License](#-license)

---

## ✨ Screenshots

**Running the App:**
![Running GarminGo in PowerShell](screenshots/GarminGo_CMD.png)
*A simple interactive menu guides you.*

**Google Sheets Output (can also be to local CSV):**
![Your data shows in a Google Sheet](screenshots/screenshot2sheets.png)
*Your Garmin data ready for analysis or AI.*

**Health and Longevity Insights in Claude:**
![Connecting your GarminGo health data to Claude](screenshots/GarminGo_Claude.png)
*Your Garmin data ready for analysis or AI in Claude, ChatGPT, or Gemini.*

**Live Googe Sheets Connection to Gemini:**
![Feed continuous GarminGo data updates to Google Sheets](screenshots/GarminGo_Gemini_Advanced.png)
*Live connection between Google Sheets and Gemini.*

---

## 🌟 Advanced Features (Added in this Fork)

This version of GarminGo has been heavily modified to support **fully automated, headless, and containerized deployments** (like running on a server via Docker and Cron).

* **Headless Automation & Cron Support:** Bypasses the interactive prompts by using Typer CLI arguments. You can pass `--start-date`, `--end-date`, `--profile`, and `--output-type` directly in your execution command. 
* **Persistent Token Storage:** Re-engineered the authentication flow using `garth.sso` and the `keyrings.alt` library. Instead of requiring a system keyring or constantly prompting for a password and MFA code, the script saves its session safely to a `config.tokens.json` file.
* **Smart Google Sheets Sync (The "Overwrite Loop"):** The original script blindly appended new rows every time it ran. This fork actively reads the `Date` column in your Google Sheet first. If it finds the date it's currently syncing, it **overwrites** that row with fresh data. If the date doesn't exist, it appends a new row. This guarantees zero duplicate rows!
* **Project Security:** Fortified the `.gitignore` file to ensure sensitive tokens, environments, and logs are never accidentally pushed to a public repository.

---

## 🔄 The Ultimate Health Data Pipeline (Omron -> Garmin -> Sheets)

You can chain GarminGo together with a tool called **[omramin](https://github.com/ikester/omramin)** (a CLI tool that syncs Omron Connect blood pressure data to Garmin Connect) to create a fully hands-off health data pipeline.

### How it works:
1. You take a blood pressure reading with an Omron cuff, and it syncs to the Omron app.
2. `omramin` pulls the reading from the Omron Cloud and pushes it to your Garmin Connect account.
3. `GarminGo` immediately pulls your updated Garmin Connect data (now containing your Omron BP reading) and pushes it to your custom Google Sheet.

### The Docker & Cron Automation Setup
Assuming you have both scripts running inside a Docker container (e.g., `garmingo-service`), you can automate the entire loop by adding a single line to your server's root crontab (`crontab -e`).

```bash
# Sync Omron to Garmin, then Garmin to Sheets every hour (Logs saved to /var/log/garmin_sync.log)
0 * * * * ( /usr/bin/docker exec garmingo-service omramin --keyring-backend file --keyring-file /root/.config/omramin/config.tokens.json sync --days 1 && /usr/bin/docker exec garmingo-service python3 src/main.py cli-sync --start-date $(date +\%Y-\%m-\%d) --end-date $(date +\%Y-\%m-\%d) --profile USER1 --output-type sheets ) >> /var/log/garmin_sync.log 2>&1

```

---

## 🛠️ Technical Documentation: Sync Pipeline

### 1. Project Overview

This project is an automated, containerized data pipeline that synchronizes health data from Omron and Garmin, ultimately exporting over 60 physiological metrics (the "Kitchen Sink") directly to a formatted Google Sheet.

* **Repository:** `https://github.com/Galletta/GarminGo`
* **Host Environment:** Fujitsu Linux Server (IP: `192.168.0.122`)
* **Deployment Path:** `/opt/garmin-sync`
* **Execution Schedule:** Daily at 08:10 AM (Europe/Bratislava)

### 2. Architecture & Containerization

The entire pipeline is packaged into a single Docker container named **`omramin-garmingo`**. This ensures the application is highly portable and isolated from the host server's system packages.

**Base Environment:**

* **Image:** `python:3.11-slim`
* **Installed System Packages:** `cron`, `git`, `tzdata`
* **Timezone:** `Europe/Bratislava` (configured via `docker-compose.yml`)

**Docker Compose Configuration:**
The `docker-compose.yml` file acts as the Infrastructure as Code (IaC) blueprint. It relies on volume mapping to ensure that sensitive credential tokens are stored safely on the host machine and are not wiped out when the container is rebuilt.

**Mapped Volumes:**

* `./garmingo:/app/garmingo`
* `./omramin:/root/.config/omramin` (Omron tokens)
* `./keyring:/root/.local/share/python_keyring` (Plaintext keyring vault)
* `./garth:/root/.garth` (Garmin session tokens)

**Key Environment Variables:**

* `PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring` (Forces Python to use a file-based keyring, necessary for headless server environments without a GUI keychain).

### 3. Automation & Scheduling (Cron)

The automation is handled by a custom `crontab` file injected directly into the container at `/etc/cron.d/sync-jobs`.

**The Cron Job:**
The task is scheduled via the following cron expression:

```text
10 8 * * *

```

At 08:10 AM daily, the container executes a chained command:

1. **Omron Sync:** `omramin --keyring-backend file --keyring-file /root/.config/omramin/config.tokens.json sync --days 1`
2. **Garmin to Sheets Sync:** `python3 src/main.py cli-sync --start-date $(date +\%Y-\%m-\%d) --end-date $(date +\%Y-\%m-\%d) --profile USER1 --output-type sheets`
3. **Log Routing:** `> /proc/1/fd/1 2>&1` (This forces the cron job's background output to bypass the hidden cron logs and print directly to the main Docker container logs so it can be viewed externally).

*Note: The `crontab` file must strictly end with an empty newline character (`\n`) to be parsed correctly by the POSIX cron daemon.*

### 4. Security & Credentials Management

To maintain a public GitHub repository while handling sensitive health and Google Drive data, strict `.gitignore` rules are enforced.

**Ignored (Secured) Files & Directories:**

* `.env` (Contains raw passwords and API keys)
* `*.json` (Protects Google Drive `credentials.json` and Omron tokens)
* `omramin/`, `keyring/`, `garth/` (Mapped volumes containing active session tokens)

*Disaster Recovery:* A compressed backup of these credentials (`credentials_backup.tar.gz`) is maintained off-server for quick restoration.

### 5. Maintenance & Useful Commands

All administrative commands should be run from the `/opt/garmin-sync` directory on the host server.

* **View Daily Sync Logs:**

```bash
docker logs omramin-garmingo

```

* **Manually Trigger a Sync inside the Container:**

```bash
docker exec omramin-garmingo sh -c "cd /app && python3 src/main.py cli-sync --start-date \$(date +%Y-%m-%d) --end-date \$(date +%Y-%m-%d) --profile USER1 --output-type sheets"

```

* **Pull Code Updates and Rebuild:**

```bash
git pull origin main
docker compose up -d --build

```

* **Check Internal Container Cron Status:**

```bash
docker exec omramin-garmingo crontab -l

```

---

## 🚀 Quick Start: Get Your Data as a CSV File

**1. 🐍 Install Python:**

* Make sure you have Python 3.9 or newer installed.
* During install, ensure you check "Add Python to PATH".

**2. 📄 Get the Code:**

* Go to the GarminGo GitHub repository page.
* Click the green "Code" button and select **"Download ZIP"**.
* Extract the downloaded ZIP file to a folder on your computer.

**3. ✨ Install the Project and Dependencies:**

* Open PowerShell or Command Prompt (CMD) in the Project Folder.
* Run the following command to install GarminGo and its required libraries:

```powershell
pip install .

```

**4. ⚙️ Configure Your Garmin Login:**

* In the project folder, make a copy of `.env.example` and rename it to `.env`.
* Fill in your Garmin Connect email and password.

---

## ⚙️ Advanced Options & Google Sheets Integration

### Optional: Use a Python Virtual Environment

For cleaner dependency management, you might want to create and activate a virtual environment before installing the project.

```bash
python -m venv venv

```

### 🔑 Google API Setup (for Google Sheets Output)

To send data to Google Sheets, you need to set up Google API credentials:

1. Go to the **Google Cloud Console**, create a project, and enable the **Google Sheets API**.
2. Go to "APIs & Services" > "Credentials" > "+ CREATE CREDENTIALS" > "OAuth client ID" (Desktop app).
3. Download the JSON credential file.
4. Create a folder named `credentials` in your GarminGo directory. Move the JSON file there and rename it `client_secret.json`.
5. Open your `.env` file and set your Sheet ID (from the Google Sheets URL) in `USER1_SHEET_ID`.

### ▶️ Running for Google Sheets Output:

❗**First Run Only:** Your web browser will open asking you to log in to your Google account and grant permission. A `token.pickle` file will be created in your `credentials` folder. From then on, it will sync automatically.

---

## 📊 Available Metrics

This tool has been heavily expanded to pull over 60 distinct health, longevity, and performance metrics directly from the Garmin API.

* **The Basics:** Daily Steps, Active/Resting Calories, Sedentary Time, Intensity Minutes.
* **Body Composition:** Weight, Body Fat %, Blood Pressure (Systolic/Diastolic), BP Logs.
* **Sleep & Recovery:** Sleep Score, Sleep Stages (Deep, Light, REM, Awake), HRV (ms), HRV Status, Overnight HR, SpO2, Respiration.
* **Nervous System & Stress:** Body Battery (High/Low/Change/Charged/Drained), Stress Durations (High/Medium/Low), Rest/Activity Durations.
* **Fitness & Training:** VO2 Max (Running/Cycling), Time in HR Zones 1-5, Aerobic/Anaerobic Training Effect.
* **Advanced Cycling:** Training Stress Score (TSS), Intensity Factor (IF), Normalized Power (NP), Max 20 Min Power.

---

## 📖 Metric Dictionary & Data Sources

Curious what these numbers actually mean or where Garmin gets them? Here is the complete breakdown of the data this script extracts:

### 1. The Basics & Daily Summary (Source: User Summary Payload)

* **Steps:** Total daily step count.
* **Active Calories:** Calories burned specifically through movement and exercise above your basal metabolic rate.
* **Resting Calories:** Your BMR (Basal Metabolic Rate); calories burned just staying alive.
* **Sedentary Time (hrs):** Time spent awake but inactive. *Crucial metric for all-cause mortality risk.*
* **Intensity Minutes:** Garmin's calculation of moderate (1x) and vigorous (2x) exercise minutes for the week/day.

### 2. Body Composition & Vitals (Source: Stats & BP Payloads)

* **Weight / Body Fat %:** Pulled from Garmin Index scales or manual entry.
* **Blood Pressure (Sys/Dia):** Pulled from the dedicated blood pressure endpoint (often populated by Omron sync). Averages multiple readings if taken on the same day.
* **Resting Heart Rate:** Your lowest 30-minute average heart rate measured over a 24-hour period.

### 3. Sleep & Overnight Recovery (Source: Sleep & HRV Payloads)

* **Sleep Score (0-100):** Garmin's overall rating of your sleep quality based on duration, stress, and stages.
* **Sleep Stages (hrs):** Breakdown of Deep, Light, REM, and Awake times. *Deep sleep drives physical recovery; REM drives cognitive recovery.*
* **HRV (ms) & Status:** Heart Rate Variability. High HRV means a resilient, relaxed nervous system. Status compares last night's average to your 3-week baseline.
* **Avg Overnight HR:** Average heart rate while sleeping.
* **SpO2 (Avg/Lowest):** Blood oxygen saturation levels during sleep.
* **Respiration / Breathing Variations:** Breaths per minute and disturbances (useful for detecting sleep apnea or illness).

### 4. Nervous System, Stress & Body Battery (Source: Stats & Summary Payloads)

* **Body Battery (0-100):** Garmin's proprietary energy metric combining HRV, stress, and sleep.
* *BB High / Low:* The peak and floor of your energy for the day.
* *BB Charged / Drained:* The total amount of energy gained (recovery) vs. lost (stress/activity) over 24 hours.
* **Average Stress (0-100):** Daily average of physiological stress (measured via inverse HRV).
* **Stress Durations (hrs):** Time spent in High, Medium, and Low sympathetic nervous system states.
* **Rest Duration (hrs):** Time spent in a parasympathetic (rest and digest) state while awake.

### 5. Fitness & General Training (Source: Training Status & Activities)

* **VO2 Max (Running/Cycling):** The maximum rate of oxygen consumption your body can utilize during intense exercise.
* **Time in Zones 1-5 (mins):** The total time spent in specific Heart Rate or Power zones across all activities for the day. *Zone 2 is critical for mitochondrial health and endurance base building.*
* **Aerobic / Anaerobic TE (0.0 - 5.0):** Training Effect. Measures how much a specific workout improved your aerobic or anaerobic capacity.

### 6. Advanced Cycling Dynamics (Source: Activities Payload)

* **TSS (Training Stress Score):** A composite number measuring the physiological toll of a ride based on duration and intensity.
* **Intensity Factor (IF):** How intense a ride was relative to your Functional Threshold Power (FTP). An IF of 1.0 means you rode exactly at your FTP for the entire ride.
* **Normalized Power (NP):** An adjusted average power metric that accounts for the physiological cost of rapid changes in effort (surges, coasting).
* **Max 20 Min Power:** Your highest average wattage sustained for 20 continuous minutes.

---

## 🛠️ Troubleshooting

* **`garmingo` Command Not Found:** Ensure your Python scripts directory is added to your system's PATH variable.
* **Garmin Login Issues:** Double-check your `.env` credentials.
* **Google Sheets Access Denied:** Ensure the Google Sheets API is enabled in Google Cloud.

## 🔒 Security Notes

* Never share or commit your `.env` file to Git or any public place, as it contains your passwords.
* The `.gitignore` file is already set up to prevent accidental commits of `.env` and the `credentials` folder.
* Keep your Google `client_secret.json` file secure.

## 📜 License

This project is licensed under the MIT License - see the `LICENSE.md` file for details.