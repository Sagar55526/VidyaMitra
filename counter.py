import threading
import time

# Dictionary to store counters for each user
user_counters = {}

def start_counter(user_id):
    """Start a counter that increases every second."""
    if user_id in user_counters:
        return  # Avoid starting multiple timers for the same user

    user_counters[user_id] = {"count": 0, "running": True}

    def run_timer():
        while user_counters[user_id]["running"]:
            time.sleep(1)  # Increment every second
            user_counters[user_id]["count"] += 1

    thread = threading.Thread(target=run_timer, daemon=True)
    thread.start()

def stop_counter(user_id):
    """Stop the counter and return the elapsed time in seconds."""
    if user_id in user_counters:
        user_counters[user_id]["running"] = False
        elapsed_time = user_counters[user_id]["count"]
        del user_counters[user_id]  # Remove after stopping
        return elapsed_time
    return 0
