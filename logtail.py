#!/usr/bin/env python3
"""
A Python implementation of 'tail -f' for continuously monitoring log files.
"""

import sys
import time
import argparse
from pathlib import Path


def tail_file(filename, interval=1.0, lines=10):
    """
    Continuously monitor a file and print new lines as they are added.
    
    Args:
        filename: Path to the file to monitor
        interval: Time in seconds between checks
        lines: Number of initial lines to display
    
    # Basic usage - monitor a log file
    python logtail.py logfile.txt

    # Show last 20 lines initially
    python logtail.py -n 20 logfile.txt

    # Skip initial lines, only show new content
    python logtail.py -n 0 logfile.txt

    # Custom check interval (0.5 seconds)
    python logtail.py -s 0.5 logfile.txt
    """
    try:
        file_path = Path(filename)
        
        if not file_path.exists():
            print(f"Error: File '{filename}' not found", file=sys.stderr)
            sys.exit(1)
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            # Move to the end of the file
            file.seek(0, 2)
            file_size = file.tell()
            
            # If requested, show last N lines
            if lines > 0:
                file.seek(0)
                all_lines = file.readlines()
                for line in all_lines[-lines:]:
                    print(line, end='')
            
            print(f"==> Monitoring {filename} for changes (Ctrl+C to stop) <==", file=sys.stderr)


# Continuously monitor the file
            while True:
                current_position = file.tell()
                line = file.readline()
                
                if line:
                    print(line, end='')
                    sys.stdout.flush()
                else:
                    # Check if file was truncated
                    file.seek(0, 2)
                    new_size = file.tell()
                    
                    if new_size < current_position:
                        # File was truncated, start from beginning
                        print("\n==> File truncated, restarting from beginning <==", file=sys.stderr)
                        file.seek(0)
                    else:
                        # No new data, wait a bit
                        time.sleep(interval)
                        
    except KeyboardInterrupt:
        print("\n==> Monitoring stopped <==", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Monitor log files continuously like tail -f'
    )
    parser.add_argument(
        'filename',
        help='Path to the log file to monitor'
    )
    parser.add_argument(
        '-n', '--lines',
        type=int,
        default=10,
        help='Number of initial lines to display (default: 10, use 0 to skip)'
    )
    parser.add_argument(
        '-s', '--sleep-interval',
        type=float,
        default=1.0,
        dest='interval',
        help='Sleep interval in seconds between checks (default: 1.0)'
    )
    
    args = parser.parse_args()
    tail_file(args.filename, args.interval, args.lines)


if __name__ == '__main__':
    main()
