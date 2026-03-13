from dataclasses import dataclass, fields
from datetime import date
from typing import Optional

# 1. The Dataclass defines the data structure
@dataclass
class GarminMetrics:
    date: date
    sleep_score: Optional[float] = None
    sleep_length: Optional[float] = None
    weight: Optional[float] = None
    body_fat: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    bp_log_raw: Optional[str] = None  # NEW: For the text log
    active_calories: Optional[int] = None
    resting_calories: Optional[int] = None
    resting_heart_rate: Optional[int] = None
    average_stress: Optional[int] = None
    training_status: Optional[str] = None
    vo2max_running: Optional[float] = None
    vo2max_cycling: Optional[float] = None
    intensity_minutes: Optional[int] = None
    all_activity_count: Optional[int] = None
    running_activity_count: Optional[int] = None
    running_distance: Optional[float] = None
    cycling_activity_count: Optional[int] = None
    cycling_distance: Optional[float] = None
    strength_activity_count: Optional[int] = None
    strength_duration: Optional[float] = None
    cardio_activity_count: Optional[int] = None
    cardio_duration: Optional[float] = None
    tennis_activity_count: Optional[int] = None
    tennis_activity_duration: Optional[float] = None
    overnight_hrv: Optional[int] = None
    hrv_status: Optional[str] = None
    steps: Optional[int] = None

    # Body Battery
    body_battery_high: Optional[int] = None
    body_battery_low: Optional[int] = None
    body_battery_change: Optional[int] = None
    
    # Respiration & SpO2
    avg_spo2: Optional[float] = None
    lowest_spo2: Optional[float] = None
    respiration_avg: Optional[float] = None
    lowest_respiration: Optional[float] = None
    breathing_variations: Optional[float] = None
    
    # Stress & Recovery
    stress_duration: Optional[int] = None
    rest_duration: Optional[int] = None
    activity_duration: Optional[int] = None
    avg_overnight_hr: Optional[int] = None
    restless_moments: Optional[int] = None
    avg_skin_temp_change: Optional[float] = None
    
    # Sleep Stages (Hours)
    deep_sleep: Optional[float] = None
    light_sleep: Optional[float] = None
    rem_sleep: Optional[float] = None
    awake_sleep: Optional[float] = None

    # Longevity & Nervous System
    sedentary_time_hrs: Optional[float] = None
    high_stress_duration_hrs: Optional[float] = None
    medium_stress_duration_hrs: Optional[float] = None
    low_stress_duration_hrs: Optional[float] = None
    bb_charged: Optional[int] = None
    bb_drained: Optional[int] = None
    
    # Advanced Cycling & Training Metrics
    time_in_zone_1_mins: Optional[float] = None
    time_in_zone_2_mins: Optional[float] = None
    time_in_zone_3_mins: Optional[float] = None
    time_in_zone_4_mins: Optional[float] = None
    time_in_zone_5_mins: Optional[float] = None

    training_stress_score: Optional[float] = None
    intensity_factor: Optional[float] = None
    norm_power: Optional[float] = None
    max_20_min_power: Optional[float] = None
    aerobic_training_effect: Optional[float] = None
    anaerobic_training_effect: Optional[float] = None

# 2. The Headers list defines the output order and names
HEADERS = [
    # --- 1. THE BASICS & DAILY SUMMARY ---
    "Date", "Steps", "Active Calories", "Resting Calories", "Sedentary Time (hrs)", 
    "Intensity Minutes", "All Activity Count",

    # --- 2. BODY COMPOSITION & VITALS ---
    "Weight (kg)", "Body Fat %",
    #"BP Systolic Avg", "BP Diastolic Avg",
    "BP Log Raw", "Resting Heart Rate",

    # --- 3. SLEEP & OVERNIGHT RECOVERY ---
    "Sleep Score", "Sleep Length", "Deep Sleep (hrs)", "Light Sleep (hrs)", "REM Sleep (hrs)", "Awake Sleep (hrs)", 
    "Restless Moments", "HRV (ms)", "HRV Status", "Avg Overnight HR", "Skin Temp Change", 
    "Avg SpO2", "Lowest SpO2", "Avg Respiration", "Lowest Respiration", "Breathing Variations",

    # --- 4. NERVOUS SYSTEM, STRESS & BODY BATTERY ---
    "BB High", "BB Low", "BB Change", "BB Charged", "BB Drained", 
    "Average Stress", "Stress Duration", "High Stress (hrs)", "Medium Stress (hrs)", "Low Stress (hrs)", 
    "Rest Duration", "Activity Duration",

    # --- 5. FITNESS & GENERAL TRAINING ---
    "Training Status", "VO2 Max Running", "VO2 Max Cycling", 
    "Time in Zone 1 (mins)", "Time in Zone 2 (mins)", "Time in Zone 3 (mins)", "Time in Zone 4 (mins)", "Time in Zone 5 (mins)", 
    "Aerobic TE", "Anaerobic TE",

    # --- 6. ACTIVITY BREAKDOWNS & ADVANCED CYCLING ---
    "Running Activity Count", "Running Distance (km)", 
    "Strength Activity Count", "Strength Duration", 
    "Cardio Activity Count", "Cardio Duration", 
    "Tennis Activity Count", "Tennis Activity Duration",
    "Cycling Activity Count", "Cycling Distance (km)", 
    "TSS", "Intensity Factor", "Normalized Power (W)", "Max 20 Min Power (W)"
]

# 3. The Map connects the Headers to the Dataclass attributes
HEADER_TO_ATTRIBUTE_MAP = {
    "Date": "date",
    "Sleep Score": "sleep_score",
    "Sleep Length": "sleep_length",
    "Weight (kg)": "weight", 
    "Body Fat %": "body_fat",
    #"BP Systolic Avg": "blood_pressure_systolic",
    #"BP Diastolic Avg": "blood_pressure_diastolic",
    "BP Log Raw": "bp_log_raw",
    "Active Calories": "active_calories",
    "Resting Calories": "resting_calories",
    "Resting Heart Rate": "resting_heart_rate",
    "Average Stress": "average_stress",
    "Training Status": "training_status",
    "VO2 Max Running": "vo2max_running",
    "VO2 Max Cycling": "vo2max_cycling",
    "Intensity Minutes": "intensity_minutes",
    "All Activity Count": "all_activity_count",
    "Running Activity Count": "running_activity_count",
    "Running Distance (km)": "running_distance",
    "Cycling Activity Count": "cycling_activity_count",
    "Cycling Distance (km)": "cycling_distance",
    "Strength Activity Count": "strength_activity_count",
    "Strength Duration": "strength_duration",
    "Cardio Activity Count": "cardio_activity_count",
    "Cardio Duration": "cardio_duration",
    "HRV (ms)": "overnight_hrv",
    "HRV Status": "hrv_status",
    "Tennis Activity Count": "tennis_activity_count",
    "Tennis Activity Duration": "tennis_activity_duration",
    "Steps": "steps",

    # Body Battery
    "BB High": "body_battery_high",
    "BB Low": "body_battery_low",
    "BB Change": "body_battery_change",
    "BB Charged": "bb_charged",
    "BB Drained": "bb_drained",
    
    # SpO2 and Respiration
    "Avg SpO2": "avg_spo2",
    "Lowest SpO2": "lowest_spo2",
    "Avg Respiration": "respiration_avg",
    "Lowest Respiration": "lowest_respiration",

    "Stress Duration": "stress_duration",
    "High Stress (hrs)": "high_stress_duration_hrs",
    "Medium Stress (hrs)": "medium_stress_duration_hrs",
    "Low Stress (hrs)": "low_stress_duration_hrs",

    "Rest Duration": "rest_duration",
    "Avg Overnight HR": "avg_overnight_hr",
    "Skin Temp Change": "avg_skin_temp_change",
    "Sedentary Time (hrs)": "sedentary_time_hrs",
    
    # Sleep Metrics
    "Deep Sleep (hrs)": "deep_sleep",
    "Light Sleep (hrs)": "light_sleep",
    "REM Sleep (hrs)": "rem_sleep",
    "Awake Sleep (hrs)": "awake_sleep",
    "Restless Moments": "restless_moments",
    "Breathing Variations": "breathing_variations",

    "Activity Duration": "activity_duration",
    "Time in Zone 1 (mins)": "time_in_zone_1_mins",
    "Time in Zone 2 (mins)": "time_in_zone_2_mins",
    "Time in Zone 3 (mins)": "time_in_zone_3_mins",
    "Time in Zone 4 (mins)": "time_in_zone_4_mins",
    "Time in Zone 5 (mins)": "time_in_zone_5_mins",
    "TSS": "training_stress_score",
    "Intensity Factor": "intensity_factor",
    "Normalized Power (W)": "norm_power",
    "Max 20 Min Power (W)": "max_20_min_power",
    "Aerobic TE": "aerobic_training_effect",
    "Anaerobic TE": "anaerobic_training_effect",

}

## Helper to get all attribute names from the dataclass
#ALL_METRIC_ATTRIBUTES = [field.name for field in fields(GarminMetrics)]
