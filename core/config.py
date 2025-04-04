import yaml
import os
import logging
from typing import Any, Dict, Optional
import sys

# Ensure core package can be found for exceptions later, not strictly needed for this file
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .exceptions import ConfigError # Use relative import

logger = logging.getLogger(__name__)

# Default path is relative to the project root where lahma.py runs
DEFAULT_CONFIG_FILENAME = "config.yaml"
CONFIG_DIR = "config"
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, DEFAULT_CONFIG_FILENAME) # e.g., config/config.yaml

def find_config_file(config_path_arg: Optional[str] = None) -> Optional[str]:
    """Finds the configuration file path to use."""
    # 1. Explicit path from argument
    if config_path_arg:
        if os.path.exists(config_path_arg):
            logger.debug(f"Using config file specified via argument: {config_path_arg}")
            return config_path_arg
        else:
            # If explicit path given but doesn't exist, raise error
            raise ConfigError(f"Config file specified via --config does not exist: {config_path_arg}")

    # 2. Default path (e.g., config/config.yaml) relative to current working dir
    #    This assumes lahma.py is run from the project root directory.
    if os.path.exists(DEFAULT_CONFIG_PATH):
         logger.debug(f"Using default config file: {DEFAULT_CONFIG_PATH}")
         return DEFAULT_CONFIG_PATH

    # 3. Example config file (as a fallback to avoid errors, maybe warn?)
    example_path = os.path.join(CONFIG_DIR, "config.example.yaml")
    if os.path.exists(example_path):
         logger.warning(f"Default config file '{DEFAULT_CONFIG_PATH}' not found. "
                        f"Falling back to example config: {example_path}. "
                        "Please copy it to config.yaml and customize.")
         return example_path

    # 4. No config file found
    logger.warning(f"No configuration file found at specified path, default path '{DEFAULT_CONFIG_PATH}', or example path.")
    return None


def load_config(config_path_arg: Optional[str] = None) -> Dict[str, Any]:
    """Loads configuration from YAML, handling defaults and environment variables."""
    config_file_to_load = find_config_file(config_path_arg)
    config: Dict[str, Any] = {} # Start with an empty config dictionary

    if config_file_to_load:
        try:
            with open(config_file_to_load, 'r') as f:
                loaded_yaml = yaml.safe_load(f)
                if isinstance(loaded_yaml, dict):
                    config = loaded_yaml
                    logger.info(f"Successfully loaded configuration from: {config_file_to_load}")
                else:
                     # Handle empty or invalid YAML structure
                     logger.warning(f"Config file '{config_file_to_load}' is empty or not a valid dictionary. Using defaults.")
                     config = {} # Reset to empty if file content is not a dict

        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config file {config_file_to_load}: {e}", exc_info=True)
            raise ConfigError(f"Invalid YAML syntax in {config_file_to_load}") from e
        except IOError as e:
            logger.error(f"Error reading config file {config_file_to_load}: {e}", exc_info=True)
            raise ConfigError(f"Cannot read config file {config_file_to_load}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading config file {config_file_to_load}: {e}", exc_info=True)
            raise ConfigError(f"Unexpected error loading config {config_file_to_load}") from e
    else:
        # No config file found, proceed with defaults and env vars only
        logger.info("No config file loaded. Relying on defaults and environment variables.")


    # --- Environment Variable Overrides & Defaults ---
    # Use LAHMA_ prefix for clarity, or fallback to common names like OPENAI_API_KEY

    # Logging Defaults (can be overridden by config file or CLI args later)
    config.setdefault('logging', {})
    config['logging'].setdefault('level', 'INFO')
    config['logging'].setdefault('file', 'lahma.log') # Default log file name

    # OpenAI Defaults & Env Var Override
    config.setdefault('openai', {})
    openai_api_key_env = os.environ.get('LAHMA_OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
    if openai_api_key_env:
        config['openai']['api_key'] = openai_api_key_env
        logger.debug("OpenAI API key loaded from environment variable.")
    elif not config['openai'].get('api_key'):
         # Only warn if honeypot module might actually need it later
         logger.debug("OpenAI API key not found in environment variables or config file.")
         # We don't raise error here, let the module handle it if needed.
    config['openai'].setdefault('model', 'gpt-3.5-turbo')
    config['openai'].setdefault('request_timeout', 60)

    # ESXi Tester Defaults
    config.setdefault('esxi_tester', {})
    config['esxi_tester'].setdefault('targets', []) # Default to empty list
    config['esxi_tester'].setdefault('check_timeout', 10)

    # Web Fuzzer Defaults
    config.setdefault('web_fuzzer', {})
    config['web_fuzzer'].setdefault('target_url', None) # No default target
    config['web_fuzzer'].setdefault('nuclei', {})
    config['web_fuzzer']['nuclei'].setdefault('templates_path', None) # Use Nuclei defaults if None
    config['web_fuzzer']['nuclei'].setdefault('extra_flags', '-silent')
    config['web_fuzzer']['nuclei'].setdefault('process_timeout', 600)

    # Tor Defaults
    config.setdefault('tor', {})
    config['tor'].setdefault('enabled', False)
    config['tor'].setdefault('control_port', 9051)
    config['tor'].setdefault('control_password', None)

    logger.debug("Configuration loading complete.")
    # logger.debug(f"Final config object (excluding sensitive values potentially): {config}") # Be careful logging config

    return config

# Example usage (will be called from lahma.py)
# cfg = load_config()
# print(cfg.get('logging', {}).get('level'))
# print(cfg.get('openai', {}).get('api_key')) # Might be None
