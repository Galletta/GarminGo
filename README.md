# 🚀 GarminGo: Make data-driven decisions about your health, fitness, and longevity! 📄📈

Pull your daily health metrics from Garmin Connect and save them directly to a user-friendly CSV file or Google Sheets.

I created this utility to feed my data into AI (e.g. LLMs like Claude, ChatGPT, and Gemini) so that I could gain insights for improving my health and longevity. Even if you aren't technical, getting your data as a CSV is pretty simple!

Once you have the files here, Python installed, and the project set up (step-by-step instructions below), you can run it by typing `garmingo`! While it's simple for non-technical users, it also supports power users, allowing you to schedule and run everything via command line arguments.

---

## Table of Contents
* [✨ Screenshots](#-screenshots)
* [🌟 Advanced Features (Added in this Fork)](#-advanced-features-added-in-this-fork)
* [🔄 The Ultimate Health Data Pipeline](#-the-ultimate-health-data-pipeline-omron---garmin---sheets)
* [🚀 Quick Start: Get Your Data as a CSV File](#-quick-start-get-your-data-as-a-csv-file)
* [⚙️ Advanced Options & Google Sheets Integration](#️-advanced-options--google-sheets-integration)
    * [Optional: Use a Python Virtual Environment](#optional-use-a-python-virtual-environment)
    * [Optional: Running as a Scheduled Task](#optional-running-as-a-scheduled-task)
    * [🔑 Google API Setup (for Google Sheets Output)](#-google-api-setup-for-google-sheets-output)
    * [▶️ Running for Google Sheets Output:](#️-running-for-google-sheets-output)
* [📊 Available Metrics](#-available-metrics)
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

* **Headless Automation & Cron Support:** Bypasses the interactive prompts by using Typer CLI arguments. You can pass `--start-date`, `--end-date`, `--profile`, and `--output-type` directly in your execution command. It also includes "headless protection" (`sys.stdin.isatty()`) so the script will gracefully exit with an error instead of hanging infinitely if accidentally run in the background without arguments.
* **Persistent Token Storage:** Re-engineered the authentication flow using `garth.sso` and the `keyrings.alt` library. Instead of requiring a system keyring (which doesn't exist in headless Docker environments) or constantly prompting for a password and MFA code, the script saves its session safely to a `config.tokens.json` file.
* **Smart Google Sheets Sync (The "Overwrite Loop"):** The original script blindly appended new rows every time it ran. This fork actively reads the `Date` column in your Google Sheet first. If it finds the date it's currently syncing, it **overwrites** that row with fresh data. If the date doesn't exist, it appends a new row. This guarantees zero duplicate rows, even if you run the sync every hour!
* **Project Security:** Fortified the `.gitignore` file to ensure sensitive tokens (`*.json`), environments (`.env`, `venv/`), and logs (`logs/`) are never accidentally pushed to a public repository.

---

## 🔄 The Ultimate Health Data Pipeline (Omron -> Garmin -> Sheets)

You can chain GarminGo together with a tool called **[omramin](https://github.com/ikester/omramin)** (a CLI tool that syncs Omron Connect blood pressure data to Garmin Connect) to create a fully hands-off health data pipeline.

### How it works:
1. You take a blood pressure reading with an Omron cuff, and it syncs to the Omron app.
2. `omramin` pulls the reading from the Omron Cloud and pushes it to your Garmin Connect account.
3. `GarminGo` immediately pulls your updated Garmin Connect data (now containing your Omron BP reading) and pushes it to your custom Google Sheet.

### The Docker & Cron Automation Setup
Assuming you have both scripts running inside a Docker container (e.g., `garmingo-service`), you can automate the entire loop by adding a single line to your server's root crontab (`crontab -e`).

First, make sure `omramin` is configured to use a file-based keyring to prevent token amnesia:
`--keyring-backend file --keyring-file /root/.config/omramin/config.tokens.json`

Then, paste this "Super Sync" command into your crontab to run the pipeline automatically at the top of every hour:

```bash
# Sync Omron to Garmin, then Garmin to Sheets every hour (Logs saved to /var/log/garmin_sync.log)
0 * * * * ( /usr/bin/docker exec garmingo-service omramin --keyring-backend file --keyring-file /root/.config/omramin/config.tokens.json sync --days 1 && /usr/bin/docker exec garmingo-service python3 src/main.py cli-sync --start-date $(date +\%Y-\%m-\%d) --end-date $(date +\%Y-\%m-\%d) --profile USER1 --output-type sheets ) >> /var/log/garmin_sync.log 2>&1

```

**Note:** The `&&` ensures that the Google Sheets sync *only* triggers if the `omramin` upload succeeds, and `$(date +\%Y-\%m-\%d)` automatically calculates today's date for GarminGo.

---

## 🚀 Quick Start: Get Your Data as a CSV File

This is the easiest way to get started and export your Garmin data.

**1. 🐍 Install Python:**

* Make sure you have Python 3.9 or newer installed. You can download it from [python.org](https://www.python.org/downloads/).
* During install, ensure you check "Add Python to PATH."

**2. 📄 Get the Code:**

* Go to the GarminGo GitHub repository page (you are probably already there).
* Click the green "Code" button (at the top right of the page) and select **"Download ZIP"**.
* Extract the downloaded ZIP file to a folder on your computer (e.g., `C:\GarminGo` or `/Users/YourName/GarminGo`).
* *(Advanced users can clone the repository using `git clone ...` if preferred).*

**3. ✨ Install the Project and Dependencies:**

* **Open PowerShell or Command Prompt (CMD) in the Project Folder:**
1. Open File Explorer and navigate to the folder where you extracted the downloaded ZIP file (e.g., `GarminGo-main`).
2. Click in the address bar at the top of File Explorer.
3. Type `powershell` and press Enter. (Alternatively, type `cmd` and press Enter).


* This opens a terminal window directly in your project folder. You should see the folder path in the prompt (e.g., `PS C:\path\to\GarminGo-main>`).


* *(Alternatively, open PowerShell/CMD from the Start Menu and use the `cd` command to navigate: `cd path\to\your\GarminGo-main`)*
* In the PowerShell or CMD window you just opened, run the following command. This will install GarminGo and all its required libraries (defined in `pyproject.toml`), making the `garmingo` command available in your terminal:
```powershell
pip install .

```


* *(For developers or if you want an "editable" install, which allows your code changes to be reflected immediately without reinstalling, you can use `pip install -e .`)*

**4. ⚙️ Configure Your Garmin Login:**

* In the project folder, find the file named `.env.example`.
* **Make a copy** of this file and **rename the copy** to just `.env`.
* Open the `.env` file with a text editor (like Notepad or VS Code).
* Find the lines starting with `USER1_` and fill in *only* your Garmin Connect email and password:
```dotenv
# User Profile 1
USER1_GARMIN_EMAIL=your_garmin_email@example.com # <-- Put your email here
USER1_GARMIN_PASSWORD=your_garmin_password     # <-- Put your password here
USER1_SHEET_ID= # <-- Leave this blank for CSV output

```


* Save the `.env` file. (You can add more `USER<N>_` profiles later if needed).

---

## ⚙️ Advanced Options & Google Sheets Integration

This section is for users who want to output data directly to Google Sheets or use Python virtual environments.

### Optional: Use a Python Virtual Environment

For cleaner dependency management, you might want to create and activate a virtual environment before installing the project.

```bash
python -m venv venv

```

Activate the virtual environment (Windows): `.\venv\Scripts\Activate.ps1`
Then, install the project: `pip install .`

### Optional: Running as a Scheduled Task

For users who wish to run GarminGo non-interactively, command-line arguments can be used. This allows you to specify parameters directly:

```bash
garmingo cli-sync --start-date YYYY-MM-DD --end-date YYYY-MM-DD --profile YOUR_PROFILE_NAME --output-type <csv_or_sheets>

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

The tool syncs the following daily metrics from Garmin Connect. *(Note: We recently expanded this list to include new fields, including Blood Pressure from the Omron integration!)*

* **Sleep & Recovery:** Sleep Score, Sleep Length, HRV (Overnight), HRV Status, Resting Heart Rate, Average Stress, Body Battery (if added to your table).
* **Body Composition & Vitals:** Weight, Body Fat Percentage, **Blood Pressure (Systolic/Diastolic)**.
* **Fitness & Activity:** Active/Resting Calories, Training Status, VO2 Max (Running/Cycling), Intensity Minutes, **Steps (Daily Step Count)**.
* **Specific Activities:** Activity Counts, Distances, and Durations (Running, Cycling, Strength, Cardio, Tennis).

*If you add any new custom metric fields to `garmin_client.py`, simply add matching headers to your Google Sheet and they will automatically sync!*

---

## 🛠️ Troubleshooting

* **`garmingo` Command Not Found:** Ensure your Python scripts directory is added to your system's PATH variable.
* **Garmin Login Issues:** Double-check your `.env` credentials and ensure MFA is correctly handled using the automated persistence flow.
* **Google Sheets Access Denied:** Ensure the Google Sheets API is enabled in Google Cloud and the account authorized has edit access to the target sheet. If you change scopes, you may need to delete `credentials/token.pickle` to force a re-login.

---

## 🔒 Security Notes

* Never share or commit your `.env` file to Git or any public place, as it contains your passwords.
* The `.gitignore` file is already set up to prevent accidental commits of `.env` and the `credentials` folder.
* Keep your Google `client_secret.json` file secure.

---

## 📜 License

This project is licensed under the MIT License - see the `LICENSE.md` file for details.
