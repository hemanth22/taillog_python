import time
import datetime
import os

log_file = "logs_test.log"

print(f"Generating logs into {os.path.abspath(log_file)}...")
print("Press Ctrl+C to stop.")

try:
    with open(log_file, "a") as f:
        f.write(f"--- Log Session Started at {datetime.datetime.now()} ---\n")
    
    counter = 1
    while True:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lorem_ipsum = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
            "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
            "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. "
            "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui "
            "officia deserunt mollit anim id est laborum."
        )
        log_message = f"[{timestamp}] INFO: Paragraph {counter}\n{lorem_ipsum}\n\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_message)
            f.flush()
            
        print(f"Wrote paragraph {counter}")
        counter += 1
        time.sleep(1) # Wait 1 second before writing the next line
        
except KeyboardInterrupt:
    print("\nLog generation stopped.")
