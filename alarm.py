import os
import time
import requests
from datetime import datetime, timedelta
import platform
from dotenv import load_dotenv

ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')

def get_user_input(prompt, validation_fn=None, error_message=None):
    """Prompts the user for input and validates it using the provided function."""
    while True:
        user_input = input(prompt)
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

def play_alarm_sound():
    """Plays an alarm sound if the platform supports it."""
    if platform.system() == 'Windows':
        import winsound
        duration = 1000 
        freq = 440  
        winsound.Beep(freq, duration)
    elif platform.system() == 'Darwin':
        os.system('say "Alarm ringing"')
    else:
        print('\a') 

def trigger_shock(api_key, shock_id, intensity, duration):
    """Sends a shock command to the OpenShock API."""
    print("Preparing to send shock with intensity:", intensity, "and duration:", duration, "milliseconds")
    
    url = 'https://api.shocklink.net/2/shockers/control'
    headers = {
        'accept': 'application/json',
        'OpenShockToken': api_key,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'shocks': [{
            'id': shock_id,
            'type': 'Shock',
            'intensity': intensity,
            'duration': duration,
            'exclusive': True
        }],
        'customName': 'AlarmShock'
    }
    
    response = requests.post(url=url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print('Shock sent successfully.')
    else:
        print(f"Failed to send shock. Response: {response.content}")

def set_alarm(alarm_time, api_key, shock_id, intensity, duration):
    """Sets an alarm for a specific time and shows a countdown."""
    duration_sec = duration / 1000
    
    print(f"Alarm set for {alarm_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Shock intensity: {intensity}")
    print(f"Shock duration: {duration_sec:.1f} seconds")
    
    while True:
        now = datetime.now()
        if now >= alarm_time:
            print("Alarm time reached! Triggering shock...")
            play_alarm_sound()
            trigger_shock(api_key, shock_id, intensity, duration)
            break

        remaining_time = alarm_time - now
        countdown_seconds = remaining_time.total_seconds()
        hours, remainder = divmod(countdown_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        print(f"Time until shock: {int(hours):02}:{int(minutes):02}:{int(seconds):02}", end='\r')
        time.sleep(1)

if __name__ == '__main__':
    SHOCK_API_KEY, SHOCK_ID = load_env()
    
    if not SHOCK_API_KEY or not SHOCK_ID:
        SHOCK_API_KEY = get_user_input("Enter your OpenShock API key: ")
        SHOCK_ID = get_user_input("Enter your OpenShock Shocker ID: ")
        
        save_env(SHOCK_API_KEY, SHOCK_ID)
    
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
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    set_alarm(alarm_time, SHOCK_API_KEY, SHOCK_ID, intensity, duration_ms)
