#!/usr/bin/env python3

import os
import sys
import subprocess
import fcntl
import time


LOCK_FILE = "/tmp/gpu_monitor.lock"
# DEFAULT_DB_PATH = os.path.expanduser("~/.config/darkenvyfanspeed.db")
# ENV_DB_VAR = "DARKENVY_FANSPEED_DB"

HYSTERESIS_RANGE = 10  # Temperature buffer range to avoid frequent fan adjustments
THROTTLING_TEMP = 83  # Temperature at which GPU throttling occurs (°C)
DEFAULT_DB_PATH = os.environ.get("DARKENVY_FANSPEED_DB", "~/.config/darkenvyfanspeed.db")



def main():
    """Main entry point for the script."""
    # Check if `nvidia-settings` is installed
    if not is_nvidia_settings_installed():
        print("You do not have 'nvidia-settings' installed.", file=sys.stderr)
        sys.exit(1)

    # Handle lock to ensure single instance
    check_existing_instance()

    # Example placeholder for further script logic
    print("Script initialized. Ready to run further logic.")


def is_nvidia_settings_installed():
    """Check if `nvidia-settings` is installed on the system."""
    result = subprocess.run(["which", "nvidia-settings"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0


def check_existing_instance():
    """Ensure only one instance of the script is running."""
    try:
        # Open the lock file
        lock_file = open(LOCK_FILE, "w")
        # Try to acquire an exclusive lock
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Write the current PID to the lock file
        lock_file.write(str(os.getpid()))
        lock_file.flush()
    except IOError:
        print("Another instance of the script is already running.", file=sys.stderr)
        sys.exit(1)


def set_fan_speed_auto():
    """Set the GPU fan speed to auto mode."""
    try:
        subprocess.run(["nvidia-settings", "-a", "[fan:0]/GPUTargetFanSpeed=0"], check=True)
        print("Fan speed set to auto mode.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set fan speed to auto mode: {e}", file=sys.stderr)
        sys.exit(1)


def set_fan_speed_manual(speed: int):
    """Set the GPU fan speed to a specific manual percentage."""
    try:
        # Ensure the speed is within valid bounds (0-100)
        if speed < 0 or speed > 100:
            raise ValueError("Fan speed must be between 0 and 100.")

        subprocess.run(
            ["nvidia-settings", "-a", f"[fan:0]/GPUTargetFanSpeed={speed}"],
            check=True
        )
        print(f"Fan speed set to {speed}%.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set manual fan speed: {e}", file=sys.stderr)
        sys.exit(1)


def get_gpu_temp_and_fan_speed():
    """Fetch the current GPU temperature and fan speed."""
    try:
        # Run the `nvidia-settings` query command
        temp_result = subprocess.run(
            ["nvidia-settings", "-q", "gpucoretemp"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        fan_result = subprocess.run(
            ["nvidia-settings", "-q", "gputargetfanspeed"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        # Parse the temperature
        temp = int(temp_result.stdout.split()[-1])
        # Parse the fan speed
        fan_speed = int(fan_result.stdout.split()[-1])
        return temp, fan_speed
    except subprocess.CalledProcessError as e:
        print(f"Error fetching GPU metrics: {e}", file=sys.stderr)
        sys.exit(1)


def adjust_fan_speed(temp: int, speed_map: dict, max_speed: int):
    """Adjust the fan speed based on the current temperature and mappings."""
    # Determine the appropriate fan speed based on the mapping
    for temp_threshold, speed in sorted(speed_map.items()):
        if temp <= temp_threshold:
            new_speed = min(speed, max_speed)
            break
    else:
        # If no match, set to maximum allowed speed
        new_speed = max_speed

    try:
        # Set the new fan speed
        set_fan_speed_manual(new_speed)
        print(f"Adjusted fan speed to {new_speed}% for temperature {temp}°C.")
    except Exception as e:
        print(f"Failed to adjust fan speed: {e}", file=sys.stderr)


def run_in_background():
    """Run the script in the background."""
    try:
        subprocess.Popen(
            [sys.executable, *sys.argv],
            start_new_session=True
        )
        print("Script is now running in the background.")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to run in background: {e}", file=sys.stderr)
        sys.exit(1)


def notify(title: str, message: str, urgency: str = "normal"):
    """Send a desktop notification using notify-send."""
    if not os.environ.get("NO_NOTIFY"):
        try:
            subprocess.run(
                ["notify-send", f"--urgency={urgency}", title, message],
                check=True
            )
        except Exception as e:
            print(f"Failed to send notification: {e}", file=sys.stderr)


def monitor_gpu(speed_map: dict, max_speed: int, cooldown: int):
    """Continuously monitor the GPU temperature and adjust fan speed."""
    last_temp = None
    last_speed = None

    try:
        while True:
            temp, current_speed = get_gpu_temp_and_fan_speed()

            # Check if temperature and fan speed adjustments are needed
            if last_temp is None or abs(temp - last_temp) > HYSTERESIS_RANGE:
                adjust_fan_speed(temp, speed_map, max_speed)
                notify("Fan Speed Adjusted", f"Temperature: {temp}°C, Fan: {current_speed}%")
                last_temp = temp
                last_speed = current_speed

            # Wait for the cooldown period
            time.sleep(cooldown)
    except KeyboardInterrupt:
        print("Monitoring interrupted by user. Resetting fan speed to auto.")
        set_fan_speed_auto()
        sys.exit(0)
    except Exception as e:
        print(f"Error during monitoring: {e}", file=sys.stderr)
        set_fan_speed_auto()
        notify("Error", f"Monitoring stopped: {e}", urgency="critical")
        sys.exit(1)


def parse_arguments():
    """Parse and return the command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="GPU Fan Speed Monitor")
    parser.add_argument(
        "-s", "--speed", choices=["slow", "medium", "fast"], default="medium",
        help="Select the fan speed mapping to use (default: medium)"
    )
    parser.add_argument(
        "-m", "--max", type=int, default=90,
        help="Maximum fan speed percentage (default: 90%)"
    )
    parser.add_argument(
        "-c", "--cooldown", type=int, default=5,
        help="Cooldown period in seconds between adjustments (default: 5 seconds)"
    )
    parser.add_argument(
        "-d", "--detach", action="store_true",
        help="Run the script in the background"
    )
    parser.add_argument(
        "--no-notify", action="store_true",
        help="Disable desktop notifications"
    )
    parser.add_argument(
        "-V", "--version", action="version", version="GPU Fan Speed Monitor v1.0"
    )

    return parser.parse_args()
