import json
from datetime import date
from typing import Dict, Any, Optional
import asyncio
import logging
import os
import garminconnect
from garth.sso import resume_login
import garth
from .exceptions import MFARequiredException
from .config import GarminMetrics

logger = logging.getLogger(__name__)

class GarminClient:
    def __init__(self, email: str, password: str):
        self.email = email # Store for manual login
        self.password = password # Store for manual login
        self.client = garminconnect.Garmin(email, password)
        self._authenticated = False
        self.mfa_ticket_dict = None
        self._auth_failed = False  # Track if authentication failed to prevent loops

    async def authenticate(self):
        """Robust authentication that forces MFA flow on any handshake failure"""
        token_dir = os.path.expanduser("~/.garth")

        def login_wrapper():
            # Try to resume if tokens exist
            if os.path.exists(token_dir) and os.listdir(token_dir):
                logger.info("Found existing tokens. Attempting resume...")
                try:
                    return self.client.login(token_dir)
                except Exception as e:
                    logger.warning(f"Resume failed: {e}. Starting fresh.")
            
            # Fresh login attempt
            logger.info("Initiating fresh login handshake...")
            return self.client.login()

        try:
            await asyncio.get_event_loop().run_in_executor(None, login_wrapper)
            self._authenticated = True
            self.client.garth.dump(token_dir)
            logger.info("Authentication successful!")

        except (Exception, AssertionError) as e:  # <--- WE NOW CATCH ASSERTION ERRORS SPECIFICALLY
            logger.info(f"Handshake interrupted: {str(e)}")
            
            # Check if we have an MFA ticket in the garth client
            if hasattr(self.client.garth, 'oauth2_token') and isinstance(self.client.garth.oauth2_token, dict):
                self.mfa_ticket_dict = self.client.garth.oauth2_token
                logger.info("MFA ticket detected. Raising MFARequiredException.")
                raise MFARequiredException(message="MFA code is required.", mfa_data=self.mfa_ticket_dict)
            
            # If no ticket, it's a real login failure
            logger.error(f"Login failed without MFA ticket: {e}")
            raise garminconnect.GarminConnectAuthenticationError(f"Authentication failed: {e}")

    async def _fetch_hrv_data(self, target_date_iso: str) -> Optional[Dict[str, Any]]:
        """Fetches HRV data for the given date."""
        # logger.info(f"Attempting to fetch HRV data for {target_date_iso}")
        try:
            hrv_data = await asyncio.get_event_loop().run_in_executor(
                None, self.client.get_hrv_data, target_date_iso
            )
            logger.debug(f"Raw HRV data for {target_date_iso}: {hrv_data}")
            return hrv_data
        except Exception as e:
            logger.error(f"Error fetching HRV data for {target_date_iso}: {str(e)}")
            return None

    async def get_metrics(self, target_date: date) -> GarminMetrics:
        logger.debug(f"VERIFY get_metrics: display_name: {getattr(self.client, 'display_name', 'Not Set')}, oauth2_token type: {type(self.client.garth.oauth2_token)}")
        if not self._authenticated:
            if self._auth_failed:
                raise Exception("Authentication has already failed. Cannot fetch metrics without successful authentication.")
            await self.authenticate()

        try:
            async def get_stats():
                return await asyncio.get_event_loop().run_in_executor(
                    None, self.client.get_stats_and_body, target_date.isoformat()
                )

            async def get_sleep():
                return await asyncio.get_event_loop().run_in_executor(
                    None, self.client.get_sleep_data, target_date.isoformat()
                )

            async def get_activities():
                return await asyncio.get_event_loop().run_in_executor(
                    None, self.client.get_activities_by_date, 
                    target_date.isoformat(), target_date.isoformat()
                )

            async def get_user_summary():
                return await asyncio.get_event_loop().run_in_executor(
                    None, self.client.get_user_summary, target_date.isoformat()
                )

            async def get_training_status():
                return await asyncio.get_event_loop().run_in_executor(
                    None, self.client.get_training_status, target_date.isoformat()
                )
            
            async def get_hrv():
                return await self._fetch_hrv_data(target_date.isoformat())

            # Explicitly fetch Blood Pressure data
            async def get_bp():
                try:
                    data = await asyncio.get_event_loop().run_in_executor(
                        None, self.client.get_blood_pressure, target_date.isoformat()
                    )
                    # BP debugging
                    # logger.info(f"DEBUG BP for {target_date.isoformat()}: {data}")
                    return data
                except Exception as e:
                    logger.debug(f"No BP data found or error fetching BP: {e}")
                    return None

            # Fetch data concurrently
            stats, sleep_data, activities, summary, training_status, hrv_payload, bp_payload = await asyncio.gather(
                get_stats(), get_sleep(), get_activities(), get_user_summary(), get_training_status(), get_hrv(), get_bp()
            )

            # Debug logging
            # logger.debug(f"Raw stats data: {stats}")
            # logger.debug(f"Raw sleep data: {sleep_data}")
            # logger.debug(f"Raw activities data: {activities}")
            # logger.debug(f"Raw summary data: {summary}")
            # logger.debug(f"Raw training status data: {training_status}")
            # logger.debug(f"Raw HRV payload: {hrv_payload}")

            # # --- TEMPORARY GARMIN RAW DATA DUMP ---
            # # This will save the raw JSON payloads to the GarminGo/raw_export/ folder
            # try:
            #     # Ensure the target directory exists before saving
            #     export_dir = "raw_export"
            #     os.makedirs(export_dir, exist_ok=True)
                
            #     with open(f"{export_dir}/raw_stats_{target_date}.json", "w") as f:
            #         json.dump(stats, f, indent=4)
            #     with open(f"{export_dir}/raw_summary_{target_date}.json", "w") as f:
            #         json.dump(summary, f, indent=4)
            #     with open(f"{export_dir}/raw_activities_{target_date}.json", "w") as f:
            #         json.dump(activities, f, indent=4)
                    
            #     logger.info(f"Saved raw JSON files for {target_date} in {export_dir}/!")
            # except Exception as e:
            #     logger.error(f"Failed to save raw JSON: {e}")
            # # --------------------------------

            # Process HRV data
            overnight_hrv_value: Optional[int] = None
            hrv_status_value: Optional[str] = None
            # Process HRV data
            if hrv_payload: # <--- Key check for hrv_payload itself
                hrv_summary = hrv_payload.get('hrvSummary') # Get hrvSummary first
                if hrv_summary: # <--- Key check for hrv_summary
                    # Safely extract hrv_value (lastNightAvg)
                    overnight_hrv_value = hrv_summary.get('lastNightAvg')

                    # Safely extract hrv_status
                    hrv_status_value = hrv_summary.get('status')
                    # logger.info(f"Extracted HRV: {overnight_hrv_value}, Status: {hrv_status_value} for {target_date}")
                else:
                    logger.warning(f"hrvSummary not found in hrv_payload for {target_date}. HRV metrics will be blank.")
            else:
                logger.warning(f"hrv_payload for {target_date} is None. HRV metrics will be blank.")


            # Process activities
            running_count = 0
            running_distance = 0
            cycling_count = 0
            cycling_distance = 0
            strength_count = 0
            strength_duration = 0
            cardio_count = 0
            cardio_duration = 0
            tennis_count = 0
            tennis_duration = 0

# Initialize metrics to None, as per GarminMetrics dataclass defaults
            sleep_score: Optional[float] = None
            sleep_length: Optional[float] = None
            weight: Optional[float] = None
            body_fat: Optional[float] = None
            blood_pressure_systolic: Optional[int] = None
            blood_pressure_diastolic: Optional[int] = None
            bp_log_raw: Optional[str] = None
            active_calories: Optional[int] = None
            resting_calories: Optional[int] = None
            intensity_minutes: Optional[int] = None
            resting_heart_rate: Optional[int] = None
            average_stress: Optional[int] = None
            vo2max_running: Optional[float] = None
            vo2max_cycling: Optional[float] = None
            training_status_phrase: Optional[str] = None
            steps: Optional[int] = None
            # Initialize all metrics to None (prevents "Variable not defined" errors)
            stress_duration: Optional[float] = None
            rest_duration: Optional[float] = None
            activity_duration: Optional[float] = None
            body_battery_high = body_battery_low = body_battery_change = None
            avg_spo2 = lowest_spo2 = respiration_avg = lowest_respiration = None
            breathing_variations = restless_moments = avg_overnight_hr = avg_skin_temp_change = None
            deep_sleep = light_sleep = rem_sleep = awake_sleep = None
            # Initialize Longevity and Training variables
            sedentary_time_hrs = high_stress_duration_hrs = medium_stress_duration_hrs = low_stress_duration_hrs = None
            bb_charged = bb_drained = None
            time_in_zone_1_mins = time_in_zone_2_mins = time_in_zone_3_mins = time_in_zone_4_mins = time_in_zone_5_mins = None
            training_stress_score = intensity_factor = None
            norm_power = max_20_min_power = aerobic_training_effect = anaerobic_training_effect = None
            acute_training_load: Optional[float] = None
            chronic_training_load: Optional[float] = None
            daily_training_load: Optional[float] = None

            if activities:
                time_in_zone_1_seconds = 0
                time_in_zone_2_seconds = 0
                time_in_zone_3_seconds = 0
                time_in_zone_4_seconds = 0
                time_in_zone_5_seconds = 0
                tss_total = 0.0
                max_if = max_np = max_20_power = max_aerobic_te = max_anaerobic_te = 0.0

                for activity in activities:
                    activity_type = activity.get('activityType', {})
                    type_key = activity_type.get('typeKey', '').lower()
                    parent_type_id = activity_type.get('parentTypeId')

                    # Existing logic for counts
                    if 'run' in type_key or parent_type_id == 1:
                        running_count += 1
                        running_distance += activity.get('distance', 0) / 1000  # Convert to km
                    elif 'ride' in type_key or 'cycling' in type_key or 'bike' in type_key or parent_type_id == 2:
                        cycling_count += 1
                        cycling_distance += activity.get('distance', 0) / 1000
                    elif 'strength' in type_key:
                        strength_count += 1
                        strength_duration += activity.get('duration', 0) / 60  # Convert seconds to minutes
                    elif 'cardio' in type_key:
                        cardio_count += 1
                        cardio_duration += activity.get('duration', 0) / 60
                    elif 'tennis' in type_key: 
                        tennis_count += 1
                        tennis_duration += activity.get('duration', 0) / 60 

                    # NEW: Aggregate Advanced Training Metrics
                    # We take the max of HR Zone 2 or Power Zone 2 to avoid double counting
                    z1_hr = activity.get('hrTimeInZone_1', 0) or 0
                    z1_power = activity.get('powerTimeInZone_1', 0) or 0
                    time_in_zone_1_seconds += max(z1_hr, z1_power)

                    z2_hr = activity.get('hrTimeInZone_2', 0) or 0
                    z2_power = activity.get('powerTimeInZone_2', 0) or 0
                    time_in_zone_2_seconds += max(z2_hr, z2_power)

                    z3_hr = activity.get('hrTimeInZone_3', 0) or 0
                    z3_power = activity.get('powerTimeInZone_3', 0) or 0
                    time_in_zone_3_seconds += max(z3_hr, z3_power)

                    z4_hr = activity.get('hrTimeInZone_4', 0) or 0
                    z4_power = activity.get('powerTimeInZone_4', 0) or 0
                    time_in_zone_4_seconds += max(z4_hr, z4_power)

                    z5_hr = activity.get('hrTimeInZone_5', 0) or 0
                    z5_power = activity.get('powerTimeInZone_5', 0) or 0
                    time_in_zone_5_seconds += max(z5_hr, z5_power)

                    tss_total += activity.get('trainingStressScore', 0) or 0
                    
                    a_if = activity.get('intensityFactor', 0) or 0
                    if a_if > max_if: max_if = a_if

                    np = activity.get('normPower', 0) or 0
                    if np > max_np: max_np = np

                    m20 = activity.get('max20MinPower', 0) or 0
                    if m20 > max_20_power: max_20_power = m20

                    aero_te = activity.get('aerobicTrainingEffect', 0) or 0
                    if aero_te > max_aerobic_te: max_aerobic_te = aero_te

                    anaero_te = activity.get('anaerobicTrainingEffect', 0) or 0
                    if anaero_te > max_anaerobic_te: max_anaerobic_te = anaero_te

                # Finalize Activity Metrics (convert seconds to mins, format nicely)
                if time_in_zone_1_seconds > 0: time_in_zone_1_mins = round(time_in_zone_1_seconds / 60, 2)
                if time_in_zone_2_seconds > 0: time_in_zone_2_mins = round(time_in_zone_2_seconds / 60, 2)
                if time_in_zone_3_seconds > 0: time_in_zone_3_mins = round(time_in_zone_3_seconds / 60, 2)
                if time_in_zone_4_seconds > 0: time_in_zone_4_mins = round(time_in_zone_4_seconds / 60, 2)
                if time_in_zone_5_seconds > 0: time_in_zone_5_mins = round(time_in_zone_5_seconds / 60, 2)
                if tss_total > 0: training_stress_score = round(tss_total, 1)
                if max_if > 0: intensity_factor = round(max_if, 3)
                if max_np > 0: norm_power = round(max_np, 1)
                if max_20_power > 0: max_20_min_power = round(max_20_power, 1)
                if max_aerobic_te > 0: aerobic_training_effect = round(max_aerobic_te, 1)
                if max_anaerobic_te > 0: anaerobic_training_effect = round(max_anaerobic_te, 1)
            else:
                logger.warning(f"Activities data for {target_date} is None. Activity metrics will be blank.")

            # Process sleep data
            if sleep_data:
                sleep_dto = sleep_data.get('dailySleepDTO', {})
                if sleep_data:
                    # A. ROOT LEVEL Metrics (Garmin-Grafana mapping)
                    # These live at the top level of the sleep_data object
                    restless_moments = sleep_data.get("restlessMomentsCount")
                    avg_overnight_hr = sleep_data.get("restingHeartRate")
                    avg_skin_temp_change = sleep_data.get("avgSkinTempDeviationC")
                
                sleep_dto = sleep_data.get('dailySleepDTO', {})
                if sleep_dto:
                    # B. DTO LEVEL Metrics
                    # Respiration & SpO2
                    avg_spo2 = sleep_dto.get('averageSpO2Value')
                    lowest_spo2 = sleep_dto.get('lowestSpO2Value')
                    respiration_avg = sleep_dto.get('averageRespirationValue')
                    lowest_respiration = sleep_dto.get('lowestRespirationValue')
                    # Breathing Disturbance (if supported by your device)
                    breathing_variations = sleep_dto.get('breathingDisruptionSeverity') # breathingDisturbanceIndex
                    
                    # Sleep Score and Stages
                    sleep_score = sleep_dto.get('sleepScores', {}).get('overall', {}).get('value')
                    deep_sleep = (sleep_dto.get('deepSleepSeconds', 0) or 0) / 3600
                    light_sleep = (sleep_dto.get('lightSleepSeconds', 0) or 0) / 3600
                    rem_sleep = (sleep_dto.get('remSleepSeconds', 0) or 0) / 3600
                    awake_sleep = (sleep_dto.get('awakeSleepSeconds', 0) or 0) / 3600
                    
                    # Sleep Duration
                    sleep_time_seconds = sleep_dto.get('sleepTimeSeconds')
                    if sleep_time_seconds and sleep_time_seconds > 0:
                        sleep_length = sleep_time_seconds / 3600
                else:
                    logger.warning(f"Daily sleep DTO not found for {target_date}.")
            else:
                logger.warning(f"Sleep data for {target_date} is None. Sleep metrics will be blank.")

            if stats:
                # Get weight and body fat
                weight = stats.get('weight', 0) / 1000 if stats.get('weight') else None  
                body_fat = stats.get('bodyFat')

                # Body Battery (High/Low & Charge/Drain)
                body_battery_high = stats.get('bodyBatteryHighestValue')
                body_battery_low = stats.get('bodyBatteryLowestValue')
                bb_charged = stats.get('bodyBatteryChargedValue')
                bb_drained = stats.get('bodyBatteryDrainedValue')
                
                # CALCULATE Body Battery Change
                if body_battery_high is not None and body_battery_low is not None:
                    body_battery_change = body_battery_high - body_battery_low
            else:
                logger.warning(f"Stats data for {target_date} is None. Weight and body fat metrics will be blank.")

            # Get blood pressure (if available)
            if bp_payload and isinstance(bp_payload, dict):
                # Garmin nests the actual readings inside measurementSummaries
                summaries = bp_payload.get('measurementSummaries', [])
                all_measurements = []
                
                for summary in summaries:
                    all_measurements.extend(summary.get('measurements', []))

                if all_measurements:
                    sys_total, dia_total, bp_count = 0, 0, 0
                    log_entries = []

                    for reading in all_measurements:
                        sys = reading.get('systolic')
                        dia = reading.get('diastolic')
                        timestamp_raw = reading.get('measurementTimestampLocal') or reading.get('measurementTimestampGMT') or ""

                        if sys and dia:
                            sys_total += sys
                            dia_total += dia
                            bp_count += 1
                            
                            # Extract HH:MM from timestamp (e.g., "2026-03-10T18:30:44.0")
                            time_str = "Unknown"
                            if "T" in timestamp_raw:
                                try:
                                    time_str = timestamp_raw.split("T")[1][:5]
                                except:
                                    pass
                            
                            log_entries.append(f"{time_str}: {sys}/{dia}")

                    if bp_count > 0:
                        blood_pressure_systolic = round(sys_total / bp_count)
                        blood_pressure_diastolic = round(dia_total / bp_count)
                        bp_log_raw = " | ".join(log_entries)

            # Fallback if dedicated endpoint is empty but stats endpoint has a single entry
            if blood_pressure_systolic is None and stats: 
                if stats.get('systolic') and stats.get('diastolic'):
                    blood_pressure_systolic = stats.get('systolic')
                    blood_pressure_diastolic = stats.get('diastolic')
                    bp_log_raw = f"Daily: {blood_pressure_systolic}/{blood_pressure_diastolic}"
            # No else needed, as they are initialized to None

            if summary:
                active_calories = summary.get('activeKilocalories')
                resting_calories = summary.get('bmrKilocalories')
                intensity_minutes = (summary.get('moderateIntensityMinutes', 0) or 0) + (2 * (summary.get('vigorousIntensityMinutes', 0) or 0))
                resting_heart_rate = summary.get('restingHeartRate')
                average_stress = summary.get('averageStressLevel')
                steps = summary.get('totalSteps')
                
                # Safely convert durations to hours AND round them so Google Sheets doesn't reject them
                raw_stress = summary.get("stressDuration")
                stress_duration = round(raw_stress / 3600, 2) if raw_stress else None
                
                raw_rest = summary.get("restStressDuration")
                rest_duration = round(raw_rest / 3600, 2) if raw_rest else None
                
                raw_activity = summary.get("activityStressDuration")
                activity_duration = round(raw_activity / 3600, 2) if raw_activity else None

                # Sedentary and Detailed Stress
                raw_sedentary = summary.get("sedentarySeconds")
                sedentary_time_hrs = round(raw_sedentary / 3600, 2) if raw_sedentary else None

                raw_high = summary.get("highStressDuration")
                high_stress_duration_hrs = round(raw_high / 3600, 2) if raw_high else None

                raw_medium = summary.get("mediumStressDuration")
                medium_stress_duration_hrs = round(raw_medium / 3600, 2) if raw_medium else None

                raw_low = summary.get("lowStressDuration")
                low_stress_duration_hrs = round(raw_low / 3600, 2) if raw_low else None
            else:
                logger.warning(f"User summary data for {target_date} is None. Summary metrics will be blank.")

            # Get VO2 max values and training status
            if training_status:
                vo2max_running = None
                vo2max_cycling = None
                most_recent_vo2max = training_status.get('mostRecentVO2Max')
                if most_recent_vo2max:
                    generic_vo2max = most_recent_vo2max.get('generic')
                    if generic_vo2max:
                        vo2max_running = generic_vo2max.get('vo2MaxValue')
                    
                    cycling_vo2max = most_recent_vo2max.get('cycling')
                    if cycling_vo2max:
                        vo2max_cycling = cycling_vo2max.get('vo2MaxValue')

                training_status_data = {} # Initialize to empty dict
                most_recent_training_status = training_status.get('mostRecentTrainingStatus')
                if most_recent_training_status:
                    latest_training_status_data = most_recent_training_status.get('latestTrainingStatusData')
                    if latest_training_status_data:
                        training_status_data = latest_training_status_data
                first_device = None
                if training_status_data:
                    # Get the first value from the dictionary, if any
                    for value in training_status_data.values():
                        first_device = value
                        break # Take the first one and exit
                
                if first_device: # Check if first_device is not None
                    training_status_phrase = first_device.get('trainingStatusFeedbackPhrase')
                    daily_training_load = first_device.get('trainingLoad')
                else:
                    training_status_phrase = None # Ensure it's None if no device data or first_device is None
                    load_balance = training_status.get('trainingLoadBalance', {}) or {}
                    acute_training_load = load_balance.get('acuteLoad')
                    chronic_training_load = load_balance.get('chronicLoad')
            else:
                logger.warning(f"Training status data for {target_date} is None. VO2 Max and training status metrics will be blank.")

            return GarminMetrics(
                date=target_date,
                sleep_score=sleep_score,
                sleep_length=sleep_length,
                weight=weight,
                body_fat=body_fat,
                blood_pressure_systolic=blood_pressure_systolic,
                blood_pressure_diastolic=blood_pressure_diastolic,
                bp_log_raw=bp_log_raw,
                active_calories=active_calories,
                resting_calories=resting_calories,
                resting_heart_rate=resting_heart_rate,
                average_stress=average_stress,
                training_status=training_status_phrase,
                vo2max_running=vo2max_running,
                vo2max_cycling=vo2max_cycling,
                intensity_minutes=intensity_minutes,
                all_activity_count=len(activities) if activities is not None else 0,
                running_activity_count=running_count,
                running_distance=running_distance,
                cycling_activity_count=cycling_count,
                cycling_distance=cycling_distance,
                strength_activity_count=strength_count,
                strength_duration=strength_duration,
                cardio_activity_count=cardio_count,
                cardio_duration=cardio_duration,
                tennis_activity_count=tennis_count, # Added for Tennis
                tennis_activity_duration=tennis_duration, # Added for Tennis
                overnight_hrv=overnight_hrv_value,
                hrv_status=hrv_status_value,
                steps=steps,
                stress_duration=stress_duration,
                rest_duration=rest_duration,
                activity_duration=activity_duration,
                body_battery_high=body_battery_high,
                body_battery_low=body_battery_low,
                body_battery_change=body_battery_change,
                avg_spo2=avg_spo2,
                lowest_spo2=lowest_spo2,
                respiration_avg=respiration_avg,
                lowest_respiration=lowest_respiration,
                breathing_variations=breathing_variations,
                restless_moments=restless_moments,
                avg_overnight_hr=avg_overnight_hr,
                avg_skin_temp_change=avg_skin_temp_change,
                deep_sleep=deep_sleep,
                light_sleep=light_sleep,
                rem_sleep=rem_sleep,
                awake_sleep=awake_sleep,
                sedentary_time_hrs=sedentary_time_hrs,
                high_stress_duration_hrs=high_stress_duration_hrs,
                medium_stress_duration_hrs=medium_stress_duration_hrs,
                low_stress_duration_hrs=low_stress_duration_hrs,
                bb_charged=bb_charged,
                bb_drained=bb_drained,
                time_in_zone_1_mins=time_in_zone_1_mins,
                time_in_zone_2_mins=time_in_zone_2_mins,
                time_in_zone_3_mins=time_in_zone_3_mins,
                time_in_zone_4_mins=time_in_zone_4_mins,
                time_in_zone_5_mins=time_in_zone_5_mins,
                training_stress_score=training_stress_score,
                intensity_factor=intensity_factor,
                norm_power=norm_power,
                max_20_min_power=max_20_min_power,
                aerobic_training_effect=aerobic_training_effect,
                anaerobic_training_effect=anaerobic_training_effect,
                acute_training_load=acute_training_load,
                chronic_training_load=chronic_training_load,
                daily_training_load=daily_training_load
            )

        except Exception as e:
            logger.error(f"Error fetching metrics for {target_date}: {str(e)}")
            # Return metrics object with just the date and potentially HRV if fetched before error
            return GarminMetrics(
                date=target_date,
                overnight_hrv=locals().get('overnight_hrv_value'), # Use locals() to get value if available
                hrv_status=locals().get('hrv_status_value')
            )

    async def submit_mfa_code(self, mfa_code: str):
        """Submits the MFA code to complete authentication."""
        if not hasattr(self, 'mfa_ticket_dict') or not self.mfa_ticket_dict:
            logger.error("MFA ticket (dict state) not available. Cannot submit MFA code.")
            raise Exception("MFA ticket (dict state) not available. Please authenticate first.")

        try:
            loop = asyncio.get_event_loop()
            # The resume_login function from garth.sso expects the garth.Client instance
            # that is awaiting MFA, and the MFA code.
            resume_login_result = await loop.run_in_executor(
                None,
                lambda: resume_login(self.mfa_ticket_dict, mfa_code) # Use the captured dict
            )
            
            logger.info(f"DEBUG: resume_login returned type: {type(resume_login_result)}")
            logger.info(f"DEBUG: resume_login returned value: {resume_login_result}")

            if isinstance(resume_login_result, tuple) and len(resume_login_result) == 2:
                oauth1_token, oauth2_token = resume_login_result
                logger.info(f"DEBUG: Unpacked OAuth1Token: {type(oauth1_token)}, {oauth1_token}")
                logger.info(f"DEBUG: Unpacked OAuth2Token: {type(oauth2_token)}, {oauth2_token}")
            else:
                logger.error(f"CRITICAL: resume_login did not return the expected tuple of tokens. Returned: {resume_login_result}")
                raise Exception("MFA token processing failed: Unexpected result from resume_login.")

            if 'client' in self.mfa_ticket_dict and isinstance(self.mfa_ticket_dict.get('client'), garth.Client):
                garth_client_instance = self.mfa_ticket_dict['client']
                logger.info(f"DEBUG: Retrieved garth_client_instance from mfa_ticket_dict: {type(garth_client_instance)}")
                
                # Explicitly set the new tokens on the garth.Client instance
                garth_client_instance.oauth1_token = oauth1_token
                garth_client_instance.oauth2_token = oauth2_token
                logger.info("DEBUG: Successfully set oauth1_token and oauth2_token on garth_client_instance.")
                logger.info(f"DEBUG: garth_client_instance.oauth2_token after update: {type(garth_client_instance.oauth2_token)}, {garth_client_instance.oauth2_token}")

                # Now, assign this updated garth_client_instance to self.client.garth
                self.client.garth = garth_client_instance
                logger.info("Successfully updated self.client.garth with the token-updated garth_client_instance from mfa_ticket_dict.")

                # New logic to populate profile details on self.client:
                try:
                    logger.info("Attempting to fetch profile details via self.client.garth.profile...")
                    # Accessing self.client.garth.profile should trigger garth to fetch it if not already cached,
                    # using the now-authenticated garth client.
                    profile_data = self.client.garth.profile
                    
                    if profile_data:
                        self.client.display_name = profile_data.get("displayName")
                        self.client.full_name = profile_data.get("fullName")
                        self.client.unit_system = profile_data.get("measurementSystem")
                        logger.info(f"Successfully populated profile details. Display name: {self.client.display_name}, Full name: {self.client.full_name}, Unit system: {self.client.unit_system}")
                    else:
                        logger.error("Failed to retrieve profile_data from self.client.garth.profile (it was None or empty).")
                        raise Exception("Failed to retrieve profile data after MFA.")

                except Exception as e_profile_fetch:
                    logger.error(f"Error fetching/setting profile details after MFA: {e_profile_fetch}", exc_info=True)
                    # This is critical for subsequent API calls, so re-raise.
                    raise Exception(f"Failed to fetch or set profile details after MFA: {e_profile_fetch}")
            else:
                logger.error(f"CRITICAL: Failed to find a valid garth.Client in self.mfa_ticket_dict['client'] after resume_login. mfa_ticket_dict['client'] is: {self.mfa_ticket_dict.get('client')}")
                raise Exception("Critical error: Could not retrieve garth.Client instance from mfa_ticket_dict post MFA for token update.")
            
            self._authenticated = True
            token_dir = os.path.expanduser("~/.garth") # FIX: Passed "~/.garth" to force the client to load previously saved session tokens, bypassing the MFA prompt on subsequent runs.
            self.client.garth.dump(token_dir)            
            self.mfa_ticket_dict = None # Clear the used MFA ticket dict
            logger.info("MFA verification successful. Garth client updated with authenticated instance.")
            return True
        except (garminconnect.GarminConnectAuthenticationError, garth.exc.GarthException) as e: # Corrected to GarthException
            self._authenticated = False
            self._auth_failed = True  # Mark auth as failed to prevent loops
            error_msg = str(e)
            logger.error(f"MFA code submission failed: {error_msg}")
            
            # Check for rate limiting
            if "429" in error_msg or "Too Many Requests" in error_msg:
                raise Exception("Garmin is rate limiting your requests. Please wait 5-10 minutes before trying again. This happens when there are too many authentication attempts in a short period.")
            elif "Invalid" in error_msg or "invalid" in error_msg:
                raise Exception("Invalid MFA code. Please check the code and try again.")
            else:
                raise Exception(f"MFA code submission failed: {error_msg}")
        except Exception as e:
            self._authenticated = False
            self._auth_failed = True  # Mark auth as failed to prevent loops
            error_msg = str(e)
            logger.error(f"An unexpected error occurred during MFA submission: {error_msg}")
            
            # Check for rate limiting in generic exceptions too
            if "429" in error_msg or "Too Many Requests" in error_msg:
                raise Exception("Garmin is rate limiting your requests. Please wait 5-10 minutes before trying again. This happens when there are too many authentication attempts in a short period.")
            else:
                raise Exception(f"An unexpected error occurred during MFA submission: {error_msg}")