
# Standard library imports
import os  # For file and path operations

# Third-party library import
import yaml  # For reading and writing YAML files


# ConfigManager is a singleton class for managing app configuration
class ConfigManager:
    _instance = None  # Holds the singleton instance

    def __init__(self):
        """
        Initialize the ConfigManager instance.
        Loads config and schema when created.
        """
        self.config = None  # Stores the current configuration
        self.schema = None  # Stores the configuration schema


    @classmethod
    def initialize(cls, schema_path=None):
        """
        Initialize the ConfigManager with the given schema path.
        Loads schema, default config, and merges user config.
        """
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.schema = cls._instance.load_config_schema(schema_path)
            cls._instance.config = cls._instance.load_default_config()
            cls._instance.load_user_config()


    @classmethod
    def get_schema(cls):
        """
        Get the configuration schema.
        Returns the schema loaded from config_schema.yaml.
        """
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")
        return cls._instance.schema


    @classmethod
    def get_config_section(cls, *keys):
        """
        Get a specific section of the configuration.
        Returns a nested section (e.g., 'model_options', 'local').
        """
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        section = cls._instance.config
        for key in keys:
            if isinstance(section, dict) and key in section:
                section = section[key]
            else:
                return {}
        return section


    @classmethod
    def get_config_value(cls, *keys):
        """
        Get a specific configuration value using nested keys.
        Returns a single value (e.g., 'sample_rate').
        """
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        value = cls._instance.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value


    @classmethod
    def set_config_value(cls, value, *keys):
        """
        Set a specific configuration value using nested keys.
        Updates the config in memory (does not save to file).
        """
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")

        config = cls._instance.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            elif not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value


    @staticmethod
    def load_config_schema(schema_path=None):
        """
        Load the configuration schema from a YAML file.
        Reads config_schema.yaml and returns its contents.
        """
        if schema_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.join(base_dir, 'config_schema.yaml')

        with open(schema_path, 'r') as file:
            schema = yaml.safe_load(file)
        return schema


    def load_default_config(self):
        """
        Load default configuration values from the schema.
        Extracts 'value' fields from schema for each setting.
        """
        def extract_value(item):
            if isinstance(item, dict):
                if 'value' in item:
                    return item['value']
                else:
                    return {k: extract_value(v) for k, v in item.items()}
            return item

        config = {}
        for category, settings in self.schema.items():
            config[category] = extract_value(settings)
        return config


    def load_user_config(self, config_path=os.path.join('src', 'config.yaml')):
        """
        Load user configuration and merge with default config.
        Reads config.yaml and updates default config with user values.
        """
        def deep_update(source, overrides):
            for key, value in overrides.items():
                if isinstance(value, dict) and key in source:
                    deep_update(source[key], value)
                else:
                    source[key] = value

        if config_path and os.path.isfile(config_path):
            try:
                with open(config_path, 'r') as file:
                    user_config = yaml.safe_load(file)
                    deep_update(self.config, user_config)
            except yaml.YAMLError:
                print("Error in configuration file. Using default configuration.")

        # Check for old VAD settings and migrate them
        if self.config.get('recording_options', {}).get('min_silence_ms') == 500:
            self.console_print("Old VAD settings detected. Migrating to new defaults.")
            self.config['recording_options']['min_silence_ms'] = 300
            self.config['recording_options']['vad_aggressiveness'] = 3
            self.config['recording_options']['energy_speech_threshold_norm'] = 0.01
            self.save_config(config_path)


    @classmethod
    def save_config(cls, config_path=os.path.join('src', 'config.yaml')):
        """
        Save the current configuration to a YAML file.
        Writes the config to config.yaml for persistence.
        """
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")
        with open(config_path, 'w') as file:
            yaml.dump(cls._instance.config, file, default_flow_style=False)


    @classmethod
    def reload_config(cls):
        """
        Reload the configuration from the file.
        Re-reads config.yaml and updates the config in memory.
        """
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized")
        cls._instance.config = cls._instance.load_default_config()
        cls._instance.load_user_config()


    @classmethod
    def config_file_exists(cls):
        """
        Check if a valid config file exists.
        Returns True if config.yaml exists in src/.
        """
        config_path = os.path.join('src', 'config.yaml')
        return os.path.isfile(config_path)


    @classmethod
    def console_print(cls, message):
        """
        Print a message to the console if enabled in the configuration.
        Only prints if 'print_to_terminal' is True in config.
        """
        if cls._instance and cls._instance.config['misc']['print_to_terminal']:
            print(message)
