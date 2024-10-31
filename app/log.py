
from datetime import datetime
import sys


def log(msg):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{date} {msg}", flush=True)
    sys.stdout.flush()
