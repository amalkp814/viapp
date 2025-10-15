 
# =============================
# settings_window.py (with comments)
# =============================
# This file defines the SettingsWindow class for viapp's settings UI.
# Beginners: This window lets you configure all options for viapp, including model, API, recording, and more.
# It reads the config schema and builds the UI dynamically, saving changes to config.yaml and .env.
#
# Key PyQt5 concepts:
# - QTabWidget: Tabbed interface for organizing settings
# - QVBoxLayout/QHBoxLayout: Layout managers for arranging widgets
# - Signals: Used to notify other parts of the app when settings are saved/closed
# - Dynamic widget creation: UI is built from the config schema
# - QMessageBox: Dialogs for help, confirmation, and info
#
# Key viapp concepts:
# - ConfigManager: Handles reading/writing config and schema
# - .env file: Stores sensitive info like API keys

import os
import sys
from dotenv import set_key, load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QMessageBox, QTabWidget, QWidget, QSizePolicy, QSpacerItem, QToolButton, QStyle, QFileDialog,
    QSpinBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QCoreApplication, QProcess, pyqtSignal

# Add parent directory to sys.path so we can import base_window and utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow
from utils import ConfigManager

# Load environment variables from .env file (for API keys, etc.)
load_dotenv()

class SettingsWindow(BaseWindow):
    # Signals to notify when settings are closed or saved
    settings_closed = pyqtSignal()
    settings_saved = pyqtSignal()
    # Emitted when settings are saved and applied without restarting the app
    settings_applied = pyqtSignal()

    def __init__(self):
        """
        Initialize the settings window.
        - Loads the config schema
        - Sets up the UI with tabs and buttons
        """
        super().__init__('Settings', 700, 700)
        self.schema = ConfigManager.get_schema()  # Get config schema (structure of all settings)
        self.init_settings_ui()

    def init_settings_ui(self):
        """
        Set up the main settings UI:
        - Creates tabs for each category (model, recording, etc.)
        - Adds Save and Reset buttons
        - Connects API/local toggle logic
        """
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.create_tabs()     # Build tabs from schema
        self.create_buttons()  # Add Save/Reset buttons

        # Connect the use_api checkbox to toggle API/local options
        self.use_api_checkbox = self.findChild(QCheckBox, 'model_options_use_api_input')
        if self.use_api_checkbox:
            self.use_api_checkbox.stateChanged.connect(lambda: self.toggle_api_local_options(self.use_api_checkbox.isChecked()))
            self.toggle_api_local_options(self.use_api_checkbox.isChecked())

    def create_tabs(self):
        """
        Create a tab for each category in the config schema (e.g. model_options, recording_options).
        Each tab contains widgets for all settings in that category.
        """
        for category, settings in self.schema.items():
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab.setLayout(tab_layout)
            self.tabs.addTab(tab, category.replace('_', ' ').capitalize())

            self.create_settings_widgets(tab_layout, category, settings)
            tab_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def create_settings_widgets(self, layout, category, settings):
        """
        Create widgets for each setting in a category.
        Handles both top-level and nested settings (e.g. model_options > api > api_key).
        """
        for sub_category, sub_settings in settings.items():
            if isinstance(sub_settings, dict) and 'value' in sub_settings:
                # Top-level setting (not nested)
                self.add_setting_widget(layout, sub_category, sub_settings, category)
            else:
                # Nested settings (e.g. api, local)
                for key, meta in sub_settings.items():
                    self.add_setting_widget(layout, key, meta, category, sub_category)

    def create_buttons(self):
        """
        Create Reset and Save buttons at the bottom of the window.
        - Reset: Reloads saved config values
        - Save: Saves changes to config.yaml and .env
        """
        reset_button = QPushButton('Reset to saved settings')
        reset_button.clicked.connect(self.reset_settings)
        self.main_layout.addWidget(reset_button)

        save_button = QPushButton('Save')
        save_button.clicked.connect(self.save_settings)
        self.main_layout.addWidget(save_button)

    def add_setting_widget(self, layout, key, meta, category, sub_category=None):
        """
        Add a single setting widget (label, input, help button) to the layout.
        Handles naming for later lookup and help tooltips.
        """
        item_layout = QHBoxLayout()
        label = QLabel(f"{key.replace('_', ' ').capitalize()}:")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        widget = self.create_widget_for_type(key, meta, category, sub_category)
        if not widget:
            return

        help_button = self.create_help_button(meta.get('description', ''))  # Tooltip/help dialog

        item_layout.addWidget(label)
        if isinstance(widget, QWidget):
            item_layout.addWidget(widget)
        else:
            item_layout.addLayout(widget)
        item_layout.addWidget(help_button)
        layout.addLayout(item_layout)

        # Set object names for later lookup (used for toggling, updating, etc.)
        widget_name = f"{category}_{sub_category}_{key}_input" if sub_category else f"{category}_{key}_input"
        label_name = f"{category}_{sub_category}_{key}_label" if sub_category else f"{category}_{key}_label"
        help_name = f"{category}_{sub_category}_{key}_help" if sub_category else f"{category}_{key}_help"
        
        label.setObjectName(label_name)
        help_button.setObjectName(help_name)
        
        if isinstance(widget, QWidget):
            widget.setObjectName(widget_name)
        else:
            # If it's a layout (for model_path), set the object name on the QLineEdit
            line_edit = widget.itemAt(0).widget()
            if isinstance(line_edit, QLineEdit):
                line_edit.setObjectName(widget_name)

    def create_widget_for_type(self, key, meta, category, sub_category):
        """
        Create a widget based on the setting's type and options.
        Supports checkboxes, dropdowns, text fields, and file pickers.
        """
        meta_type = meta.get('type')
        current_value = self.get_config_value(category, sub_category, key, meta)

        if meta_type == 'bool':
            return self.create_checkbox(current_value, key)
        elif meta_type == 'str' and 'options' in meta:
            return self.create_combobox(current_value, meta['options'])
        elif meta_type == 'str':
            return self.create_line_edit(current_value, key)
        elif meta_type == 'int':
            return self.create_int_spinbox(current_value)
        elif meta_type == 'float':
            return self.create_float_spinbox(current_value)
        return None

    def create_checkbox(self, value, key):
        """
        Create a checkbox widget for boolean settings.
        Special handling for 'use_api' to allow toggling API/local options.
        """
        widget = QCheckBox()
        widget.setChecked(value)
        if key == 'use_api':
            widget.setObjectName('model_options_use_api_input')
        return widget

    def create_combobox(self, value, options):
        """
        Create a dropdown (combobox) for settings with predefined options.
        """
        widget = QComboBox()
        widget.addItems(options)
        widget.setCurrentText(value)
        return widget

    def create_line_edit(self, value, key=None):
        """
        Create a text field for string/int/float settings.
        - For 'api_key', hides text for security
        - For 'model_path', adds a Browse button for file selection
        """
        widget = QLineEdit(value)
        if key == 'api_key':
            widget.setEchoMode(QLineEdit.Password)
            widget.setText(os.getenv('OPENAI_API_KEY') or value)
        elif key == 'model_path':
            layout = QHBoxLayout()
            layout.addWidget(widget)
            browse_button = QPushButton('Browse')
            browse_button.clicked.connect(lambda: self.browse_model_path(widget))
            layout.addWidget(browse_button)
            layout.setContentsMargins(0, 0, 0, 0)
            container = QWidget()
            container.setLayout(layout)
            return container
        # Special UX for activation hotkey: hint about format and a compact placeholder
        if key == 'activation_key':
            widget.setPlaceholderText('e.g. f9 or ctrl+shift+space')
            widget.setToolTip('Enter a single key (f1..f12) or modifier combo like ctrl+shift+space')
        return widget

    def create_int_spinbox(self, value):
        box = QSpinBox()
        try:
            box.setRange(0, 60000)
            box.setValue(int(value) if value is not None else 0)
        except Exception:
            box.setValue(0)
        return box

    def create_float_spinbox(self, value):
        box = QDoubleSpinBox()
        try:
            box.setDecimals(3)
            box.setRange(0.0, 1.0)
            box.setSingleStep(0.01)
            box.setValue(float(value) if value is not None else 0.0)
        except Exception:
            box.setValue(0.0)
        return box

    def create_help_button(self, description):
        """
        Create a help button with a tooltip and info dialog for each setting.
        """
        help_button = QToolButton()
        help_button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))
        help_button.setAutoRaise(True)
        help_button.setToolTip(description)
        help_button.setCursor(Qt.PointingHandCursor)
        help_button.setFocusPolicy(Qt.TabFocus)
        help_button.clicked.connect(lambda: self.show_description(description))
        return help_button

    def get_config_value(self, category, sub_category, key, meta):
        """
        Get the current value for a setting from the config, falling back to the default in the schema.
        """
        if sub_category:
            return ConfigManager.get_config_value(category, sub_category, key) or meta['value']
        return ConfigManager.get_config_value(category, key) or meta['value']

    def browse_model_path(self, widget):
        """
        Open a file dialog to select a Whisper model file for local transcription.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Whisper Model File", "", "Model Files (*.bin);;All Files (*)")
        if file_path:
            widget.setText(file_path)

    def show_description(self, description):
        """
        Show a popup dialog with a description for a setting (when help button is clicked).
        """
        QMessageBox.information(self, 'Description', description)

    def validate_activation_key(self, key_str: str) -> bool:
        """
        Very small heuristic validator for activation_key strings.
        Accepts:
         - f1..f24
         - single keys like 'a', 'enter', 'space'
         - modifier combos like 'ctrl+shift+space'
        """
        if not key_str:
            return False
        parts = [p.strip().lower() for p in key_str.split('+') if p.strip()]
        if not parts:
            return False
        # allow function keys
        if len(parts) == 1 and parts[0].startswith('f') and parts[0][1:].isdigit():
            num = int(parts[0][1:])
            return 1 <= num <= 24
        # allow modifier combos — check last part is non-empty
        mods = {'ctrl', 'shift', 'alt', 'meta'}
        if len(parts) >= 2:
            # all but last should be modifiers
            for p in parts[:-1]:
                if p not in mods:
                    return False
            # last can be any reasonable key (letter, number, space, enter or f-key)
            last = parts[-1]
            if last == 'space' or last == 'enter' or last.isalpha() or last.isdigit() or (last.startswith('f') and last[1:].isdigit()):
                return True
        # fallback: allow single letters/numbers
        if len(parts) == 1 and (parts[0].isalpha() or parts[0].isdigit()):
            return True
        return False

    def save_settings(self):
        """
        Save all settings to config.yaml and .env file.
        - Iterates over all widgets and stores their values
        - API key is saved securely to .env
        - Shows confirmation dialog and restarts app
        """
        # Validate activation_key before saving
        activation_widget = self.findChild(QWidget, 'recording_options_activation_key_input')
        if activation_widget and hasattr(activation_widget, 'text'):
            candidate = activation_widget.text().strip()
            if candidate:
                if not self.validate_activation_key(candidate):
                    QMessageBox.warning(self, 'Invalid Shortcut', 'Activation key format is not supported. Use a function key (e.g. f9) or modifiers like ctrl+shift+space.')
                    return

        self.iterate_settings(self.save_setting)

        # Save the API key to the .env file
        api_key = ConfigManager.get_config_value('model_options', 'api', 'api_key') or ''
        set_key('.env', 'OPENAI_API_KEY', api_key)
        os.environ['OPENAI_API_KEY'] = api_key

        # Remove the API key from the config (security)
        ConfigManager.set_config_value(None, 'model_options', 'api', 'api_key')

        ConfigManager.save_config()

        # After saving, offer the user a choice to apply settings without restarting
        resp = QMessageBox.question(
            self,
            'Settings Saved',
            'Settings have been saved. Do you want to apply them now without restarting? (Yes = apply now, No = restart app)',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if resp == QMessageBox.Yes:
            # Apply without restart
            QMessageBox.information(self, 'Settings Applied', 'Settings applied. Some changes (like API keys) may require a restart.')
            self.settings_applied.emit()
            self.close()
        else:
            # Fall back to the previous behavior: ask to restart to apply all changes
            QMessageBox.information(self, 'Restart Required', 'The application will now restart to apply all changes.')
            self.settings_saved.emit()
            self.close()

    def save_setting(self, widget, category, sub_category, key, meta):
        """
        Save a single setting value from a widget to the config.
        """
        value = self.get_widget_value_typed(widget, meta.get('type'))
        if sub_category:
            ConfigManager.set_config_value(value, category, sub_category, key)
        else:
            ConfigManager.set_config_value(value, category, key)

    def reset_settings(self):
        """
        Reset all settings to the last saved values (undo unsaved changes).
        """
        ConfigManager.reload_config()
        self.update_widgets_from_config()

    def update_widgets_from_config(self):
        """
        Update all widgets in the UI with values from the current config file.
        """
        self.iterate_settings(self.update_widget_value)

    def update_widget_value(self, widget, category, sub_category, key, meta):
        """
        Update a single widget with the value from the config file.
        """
        if sub_category:
            config_value = ConfigManager.get_config_value(category, sub_category, key)
        else:
            config_value = ConfigManager.get_config_value(category, key)

        self.set_widget_value(widget, config_value, meta.get('type'))

    def set_widget_value(self, widget, value, value_type):
        """
        Set the value of a widget (checkbox, dropdown, text field, etc.)
        """
        if isinstance(widget, QCheckBox):
            widget.setChecked(value)
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(value)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else '')
        elif isinstance(widget, QSpinBox):
            try:
                widget.setValue(int(value) if value is not None else 0)
            except Exception:
                pass
        elif isinstance(widget, QDoubleSpinBox):
            try:
                widget.setValue(float(value) if value is not None else 0.0)
            except Exception:
                pass
        elif isinstance(widget, QWidget) and widget.layout():
            # This is for the model_path widget
            line_edit = widget.layout().itemAt(0).widget()
            if isinstance(line_edit, QLineEdit):
                line_edit.setText(str(value) if value is not None else '')

    def get_widget_value_typed(self, widget, value_type):
        """
        Get the value from a widget, converting to the correct type (bool, int, float, str).
        """
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QComboBox):
            return widget.currentText() or None
        elif isinstance(widget, QLineEdit):
            text = widget.text()
            # Treat explicit 'None'/'null' strings as None (case-insensitive)
            if isinstance(text, str) and text.strip().lower() in ('none', 'null'):
                return None
            if value_type == 'int':
                return int(text) if text else None
            elif value_type == 'float':
                return float(text) if text else None
            else:
                return text or None
        elif isinstance(widget, QWidget) and widget.layout():
            # This is for the model_path widget
            line_edit = widget.layout().itemAt(0).widget()
            if isinstance(line_edit, QLineEdit):
                return line_edit.text() or None
        elif isinstance(widget, QSpinBox):
            return int(widget.value())
        elif isinstance(widget, QDoubleSpinBox):
            return float(widget.value())
        return None

    def toggle_api_local_options(self, use_api):
        """
        Show/hide API and local model options depending on the 'use_api' checkbox.
        """
        self.iterate_settings(lambda w, c, s, k, m: self.toggle_widget_visibility(w, c, s, k, use_api))

    def toggle_widget_visibility(self, widget, category, sub_category, key, use_api):
        """
        Show/hide individual widgets, labels, and help buttons for API/local settings.
        """
        if sub_category in ['api', 'local']:
            widget.setVisible(use_api if sub_category == 'api' else not use_api)
            # Also toggle visibility of the corresponding label and help button
            label = self.findChild(QLabel, f"{category}_{sub_category}_{key}_label")
            help_button = self.findChild(QToolButton, f"{category}_{sub_category}_{key}_help")
            if label:
                label.setVisible(use_api if sub_category == 'api' else not use_api)
            if help_button:
                help_button.setVisible(use_api if sub_category == 'api' else not use_api)


    def iterate_settings(self, func):
        """
        Iterate over all settings widgets and apply a function (save, update, toggle, etc.) to each.
        """
        for category, settings in self.schema.items():
            for sub_category, sub_settings in settings.items():
                if isinstance(sub_settings, dict) and 'value' in sub_settings:
                    widget = self.findChild(QWidget, f"{category}_{sub_category}_input")
                    if widget:
                        func(widget, category, None, sub_category, sub_settings)
                else:
                    for key, meta in sub_settings.items():
                        widget = self.findChild(QWidget, f"{category}_{sub_category}_{key}_input")
                        if widget:
                            func(widget, category, sub_category, key, meta)

    def closeEvent(self, event):
        """
        Confirm before closing the settings window if there are unsaved changes.
        If user chooses Yes, revert to last saved config and close.
        If No, keep the window open.
        """
        reply = QMessageBox.question(
            self,
            'Close without saving?',
            'Are you sure you want to close without saving?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            ConfigManager.reload_config()  # Revert to last saved configuration
            self.update_widgets_from_config()
            self.settings_closed.emit()
            super().closeEvent(event)
        else:
            event.ignore()
