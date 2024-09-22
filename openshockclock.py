import os
import time
import requests
from datetime import datetime, timedelta
import platform
from dotenv import load_dotenv
import configparser

ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.txt')

def get_user_input(prompt, validation_fn=None, error_message=None):
    """Prompts the user for input and validates it using the provided function."""
    while True:
        user_input = input(prompt).strip()
        if validation_fn:
            if validation_fn(user_input):
                return user_input
            else:
                print(error_message)
        else:
            return user_input

def save_env(api_key, shock_id):
    """Saves the API key and Shock ID to a .env file."""
    with open(ENV_FILE, 'w') as f:
        f.write(f"SHOCK_API_KEY={api_key}\n")
        f.write(f"SHOCK_ID={shock_id}\n")

def load_env():
    """Loads the API key and Shock ID from the .env file."""
    if os.path.exists(ENV_FILE):
        load_dotenv(ENV_FILE)
        api_key = os.getenv('SHOCK_API_KEY')
        shock_id = os.getenv('SHOCK_ID')
        return api_key, shock_id
    return None, None

def load_config():
    """Loads saved alarms from the config.txt file."""
    alarms = {}
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        for section in config.sections():
            alarm_time = datetime.strptime(config[section]['time'], '%Y-%m-%d %H:%M:%S')
            intensity = int(config[section]['intensity'])
            duration = int(config[section]['duration'])
            vibrate_before = config[section].getboolean('vibrate_before', fallback=False)
            alarms[section] = (alarm_time, intensity, duration, vibrate_before)
    return alarms

def save_alarm_to_config(alarm_name, alarm_time, intensity, duration, vibrate_before):
    """Saves an alarm to the config.txt file."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)

    config[alarm_name] = {
        'time': alarm_time.strftime('%Y-%m-%d %H:%M:%S'),
        'intensity': str(intensity),
        'duration': str(duration),
        'vibrate_before': str(vibrate_before)
    }

    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def trigger_shock(api_key, shock_id, intensity, duration, shock_type='Shock'):
    """Sends a shock or vibrate command to the OpenShock API."""
    print(f"Preparing to send {shock_type.lower()} with intensity:", intensity, "and duration:", duration, "milliseconds")

    url = 'https://api.shocklink.net/2/shockers/control'
    headers = {
        'accept': 'application/json',
        'OpenShockToken': api_key,
        'Content-Type': 'application/json'
    }

    payload = {
        'shocks': [{
            'id': shock_id,
            'type': shock_type,
            'intensity': intensity,
            'duration': duration,
            'exclusive': True
        }],
        'customName': 'OpenShockClock'
    }

    response = requests.post(url=url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f'{shock_type} sent successfully.')
    else:
        print(f"Failed to send {shock_type.lower()}. Response: {response.content}")

def set_alarms(alarms, api_key, shock_id):
    """Sets multiple alarms and monitors them."""
    vibration_sent = {name: False for name in alarms}
    while True:
        now = datetime.now()
        for name, (alarm_time, intensity, duration, vibrate_before) in list(alarms.items()):
            if vibrate_before and not vibration_sent[name] and alarm_time - timedelta(minutes=1) <= now < alarm_time:
                print(f"Pre-alarm vibration for '{name}' triggered at {now.strftime('%Y-%m-%d %H:%M:%S')}!")
                trigger_shock(api_key, shock_id, 100, 5000, 'Vibrate')
                vibration_sent[name] = True

            if now >= alarm_time:
                print(f"Alarm '{name}' time reached at {alarm_time.strftime('%Y-%m-%d %H:%M:%S')}! Triggering shock...")
                trigger_shock(api_key, shock_id, intensity, duration)

                new_alarm_time = alarm_time + timedelta(days=1)
                alarms[name] = (new_alarm_time, intensity, duration, vibrate_before)
                vibration_sent[name] = False  # Reset the vibration sent flag
                print(f"Alarm '{name}' has been reset for the next day at {new_alarm_time.strftime('%Y-%m-%d %H:%M:%S')}.")

        print("\033c", end="")
        print("\nCurrent Alarms:")
        for name, (alarm_time, intensity, duration, vibrate_before) in alarms.items():
            remaining_time = alarm_time - now
            countdown_seconds = remaining_time.total_seconds()
            hours, remainder = divmod(countdown_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            print(f"{name}: Time until shock: {int(hours):02}:{int(minutes):02}:{int(seconds):02} | "
                  f"Alarm Time: {alarm_time.strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"Intensity: {intensity} | Duration: {duration / 1000:.1f} seconds | "
                  f"Pre-alarm Vibration: {'Yes' if vibrate_before else 'No'}")

        time.sleep(1)

def add_alarm():
    """Prompts the user to add a new alarm."""
    intensity = int(get_user_input(
        "Enter shock intensity (0-100): ",
        lambda x: x.isdigit() and 0 <= int(x) <= 100,
        "Please enter a valid number between 0 and 100."
    ))

    duration_sec = float(get_user_input(
        "Enter shock duration in seconds (0.3-30): ",
        lambda x: x.replace('.', '', 1).isdigit() and 0.3 <= float(x) <= 30,
        "Please enter a valid number between 0.3 and 30."
    ))
    duration_ms = int(duration_sec * 1000)

    alarm_time_str = get_user_input("Enter the alarm time (HH:MM format): ")
    alarm_time = datetime.strptime(alarm_time_str, "%H:%M").replace(
        year=datetime.now().year,
        month=datetime.now().month,
        day=datetime.now().day
    )

    if alarm_time < datetime.now():
        alarm_time += timedelta(days=1)

    vibrate_before = get_user_input("Do you want a vibration 1 minute before the alarm? (yes/no): ").strip().lower() in ['y', 'yes']

    alarm_name = get_user_input("Enter a name for this alarm: ")

    return alarm_name, (alarm_time, intensity, duration_ms, vibrate_before)

if __name__ == '__main__':
    SHOCK_API_KEY, SHOCK_ID = load_env()

    if not SHOCK_API_KEY or not SHOCK_ID:
        print("To get your OpenShock API key, go to openshock.app, click the hamburger (three lines) menu, "
              "go to 'API Tokens', click the green + icon, name the API 'Alarm', and copy the code.")

        SHOCK_API_KEY = get_user_input("Enter your OpenShock API key: ")

        print("To get your OpenShock Shocker ID, go to openshock.app, click the hamburger (three lines) menu, "
              "go to 'Shockers', click the three vertical dots next to your device, select 'edit', and copy the ID.")

        SHOCK_ID = get_user_input("Enter your OpenShock Shocker ID: ")

        save_env(SHOCK_API_KEY, SHOCK_ID)

    alarms = load_config()

    selected_alarms = {}
    if alarms:
        print("Saved alarms:")
        for idx, name in enumerate(alarms, 1):
            print(f"{idx}. {name}")

        load_saved = get_user_input("Do you want to load a saved alarm? (yes/no): ").strip().lower()
        if load_saved in ['y', 'yes']:
            while True:
                alarm_identifier = get_user_input("Enter the number or name of the saved alarm to load: ")
                if alarm_identifier.isdigit() and 1 <= int(alarm_identifier) <= len(alarms):
                    alarm_name = list(alarms.keys())[int(alarm_identifier) - 1]
                    selected_alarms[alarm_name] = alarms[alarm_name]
                elif alarm_identifier in alarms:
                    selected_alarms[alarm_identifier] = alarms[alarm_identifier]
                else:
                    print("Invalid selection. Please enter a valid number or name.")

                more_load = get_user_input("Do you want to load another saved alarm? (yes/no): ").strip().lower()
                if more_load not in ['y', 'yes']:
                    break

    alarms = selected_alarms

    while True:
        add_new_alarm = get_user_input("Do you want to add a new alarm? (yes/no): ").strip().lower()
        if add_new_alarm in ['y', 'yes']:
            alarm_name, alarm_details = add_alarm()
            alarms[alarm_name] = alarm_details

            save_alarm_option = get_user_input("Do you want to save this alarm? (yes/no): ").strip().lower()
            if save_alarm_option in ['y', 'yes']:
                save_alarm_to_config(alarm_name, *alarm_details)
        else:
            break

    if not alarms:
        print("No alarms set. Exiting the program.")
    else:
        set_alarms(alarms, SHOCK_API_KEY, SHOCK_ID)
