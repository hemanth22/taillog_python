import time
import sys

def tail_test(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        f.seek(0, 2)
        print("Tailing started...")
        while True:
            line = f.readline()
            if not line:
                # Clear the EOF flag
                f.seek(f.tell())
                time.sleep(0.5)
                continue
            print(f"NEW LINE: {line}", end='')

if __name__ == "__main__":
    tail_test("logs_test.log")
