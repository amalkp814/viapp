import os
import sys
import subprocess

print('Starting viapp...')
subprocess.run([sys.executable, os.path.join('src', 'main.py')])
