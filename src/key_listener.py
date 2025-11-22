from pynput import keyboard
from typing import Callable, Set

from utils import ConfigManager


class KeyListener:
    """
    A class to listen for a specific key combination using pynput.
    It supports global hotkeys to trigger application actions.
    """

    def __init__(self):
        """
        Initialize the KeyListener.
        Sets up the callback registry, pressed keys tracker, and the keyboard listener.
        """
        self.callbacks = {"on_activate": [], "on_deactivate": []}
        self.pressed_keys = set()
        self.activation_keys = self.parse_key_combination()
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )

    def parse_key_combination(self) -> Set:
        """
        Parse the activation key combination from the config.
        Converts string representations of keys (e.g., 'ctrl+alt+k') into pynput Key objects.
        
        Returns:
            Set: A set of pynput Key objects representing the activation combination.
        """
        key_combination = ConfigManager.get_config_value(
            "recording_options", "activation_key"
        )
        keys = set()
        for key in key_combination.split("+"):
            key = key.strip().lower()
            if key == "ctrl":
                keys.add(keyboard.Key.ctrl)
            elif key == "alt":
                keys.add(keyboard.Key.alt)
            elif key == "shift":
                keys.add(keyboard.Key.shift)
            elif key == "f9":
                keys.add(keyboard.Key.f9)
            else:
                try:
                    keys.add(keyboard.KeyCode.from_char(key))
                except AttributeError:
                    print(f"Unknown key: {key}")
        return keys

    def on_press(self, key):
        """
        Handle key press events.
        Updates the set of pressed keys and checks if the activation combination is met.
        
        Args:
            key: The key that was pressed.
        """
        was_active = self.is_active()
        if key in self.activation_keys:
            self.pressed_keys.add(key)
        
        # Trigger activation callback if the state changed from inactive to active
        if not was_active and self.is_active():
            self._trigger_callbacks("on_activate")

    def on_release(self, key):
        """
        Handle key release events.
        Updates the set of pressed keys and checks if the activation combination is broken.
        
        Args:
            key: The key that was released.
        """
        was_active = self.is_active()
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        
        # Trigger deactivation callback if the state changed from active to inactive
        if was_active and not self.is_active():
            self._trigger_callbacks("on_deactivate")

    def is_active(self) -> bool:
        """
        Check if the activation key combination is currently pressed.
        
        Returns:
            bool: True if all activation keys are pressed, False otherwise.
        """
        return self.pressed_keys == self.activation_keys

    def start(self):
        """
        Start the key listener thread.
        """
        self.listener.start()

    def stop(self):
        """
        Stop the key listener thread.
        """
        self.listener.stop()

    def add_callback(self, event: str, callback: Callable):
        """
        Add a callback function for a specific event.
        
        Args:
            event (str): The event name ('on_activate' or 'on_deactivate').
            callback (Callable): The function to call when the event occurs.
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def _trigger_callbacks(self, event: str):
        """
        Trigger all callbacks associated with a specific event.
        
        Args:
            event (str): The event name to trigger.
        """
        for callback in self.callbacks.get(event, []):
            callback()
