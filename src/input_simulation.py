
# Standard library imports
import subprocess  # For running external commands and processes
import os  # For interacting with the operating system
import signal  # For sending signals to processes
import time  # For delays between keystrokes

# Third-party library import
from pynput.keyboard import Controller as PynputController  # For simulating keyboard input

# Local module import
from utils import ConfigManager  # For configuration management


# Helper function to run a shell command and exit if it fails
def run_command_or_exit_on_failure(command):
    """
    Run a shell command and exit if it fails.

    Args:
        command (list): The command to run as a list of strings.
    """
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        exit(1)


# Class to simulate keyboard input using different methods (pynput, dotool, ydotool)
class InputSimulator:
    """
    A class to simulate keyboard input using various methods.
    Supports pynput (cross-platform), dotool, and ydotool (Linux tools).
    """

    def __init__(self):
        """
        Initialize the InputSimulator with the specified configuration.
        Chooses the input method based on config and sets up required resources.
        """
        self.input_method = ConfigManager.get_config_value('post_processing', 'input_method')
        self.dotool_process = None  # Process for dotool (if used)

        if self.input_method == 'pynput':
            self.keyboard = PynputController()  # Create pynput keyboard controller
        elif self.input_method == 'dotool':
            self._initialize_dotool()  # Start dotool process


    def _initialize_dotool(self):
        """
        Initialize the dotool process for input simulation.
        Starts the dotool process and prepares to send commands to it.
        """
        self.dotool_process = subprocess.Popen("dotool", stdin=subprocess.PIPE, text=True)
        assert self.dotool_process.stdin is not None


    def _terminate_dotool(self):
        """
        Terminate the dotool process if it's running.
        Sends SIGINT to stop the process and cleans up.
        """
        if self.dotool_process:
            os.kill(self.dotool_process.pid, signal.SIGINT)
            self.dotool_process = None


    def typewrite(self, text):
        """
        Simulate typing the given text with the specified interval between keystrokes.

        Args:
            text (str): The text to type.
        """
        interval = ConfigManager.get_config_value('post_processing', 'writing_key_press_delay')
        # Choose typing method based on config
        if self.input_method == 'pynput':
            self._typewrite_pynput(text, interval)
        elif self.input_method == 'ydotool':
            self._typewrite_ydotool(text, interval)
        elif self.input_method == 'dotool':
            self._typewrite_dotool(text, interval)


    def _typewrite_pynput(self, text, interval):
        """
        Simulate typing using pynput.

        Args:
            text (str): The text to type.
            interval (float): The interval between keystrokes in seconds.
        """
        for char in text:
            self.keyboard.press(char)   # Press the key
            self.keyboard.release(char) # Release the key
            time.sleep(interval)        # Wait before next key


    def _typewrite_ydotool(self, text, interval):
        """
        Simulate typing using ydotool (Linux tool).

        Args:
            text (str): The text to type.
            interval (float): The interval between keystrokes in seconds.
        """
        cmd = "ydotool"
        run_command_or_exit_on_failure([
            cmd,
            "type",
            "--key-delay",
            str(interval * 1000),  # Convert seconds to milliseconds
            "--",
            text,
        ])


    def _typewrite_dotool(self, text, interval):
        """
        Simulate typing using dotool (Linux tool).

        Args:
            text (str): The text to type.
            interval (float): The interval between keystrokes in seconds.
        """
        assert self.dotool_process and self.dotool_process.stdin
        # Set the delay between keystrokes
        self.dotool_process.stdin.write(f"typedelay {interval * 1000}\n")
        # Send the type command with the text
        self.dotool_process.stdin.write(f"type {text}\n")
        self.dotool_process.stdin.flush()


    def cleanup(self):
        """
        Perform cleanup operations, such as terminating the dotool process.
        Should be called when the app exits to avoid orphaned processes.
        """
        if self.input_method == 'dotool':
            self._terminate_dotool()
