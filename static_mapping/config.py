import configparser
import os

def load_config(config_file='config.ini'):
    """Loads configuration from a .ini file."""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file '{config_file}' not found. Please create it from 'config.ini.example'.")

    config = configparser.ConfigParser()
    config.read(config_file)
    return config