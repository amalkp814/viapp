"""
run.py
-------------------
This is the main entry point for viapp.
Beginners: Run this file to start the app. It loads environment variables and launches the main GUI.
"""

import os  # For file and path operations
import sys  # For accessing the Python interpreter
import subprocess  # For running other Python scripts
from dotenv import load_dotenv  # For loading environment variables from .env files

# Print a message to the terminal so the user knows the app is starting
print('Starting viapp...')

# Load environment variables from a .env file (if present)
load_dotenv()

# Run the main application (src/main.py) using the current Python interpreter
subprocess.run([sys.executable, os.path.join('src', 'main.py')])
