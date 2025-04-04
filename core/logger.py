import logging
import sys
import os
from typing import Union # Added Union

# Determine a writable directory for logs, default to project root if possible
LOG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Project root

# Changed type hint to use Union[str, None]
def setup_logging(log_level_str: str = 'INFO', log_file_name: Union[str, None] = "lahma.log"):
    """Configures logging for the application."""
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Basic configuration sets up console logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # Ensure existing handlers are removed before basicConfig if re-configuring
    # But basicConfig replaces handlers anyway, so this setup sequence is okay.
    logging.basicConfig(level=log_level, format=log_format, stream=sys.stdout, force=True)

    root_logger = logging.getLogger() # Get root logger AFTER basicConfig

    # File Handler (Optional)
    if log_file_name:
        log_file_path = os.path.join(LOG_DIR, log_file_name)
        try:
            # Check if directory is writable, fallback if needed (though LOG_DIR should be okay)
            if not os.access(LOG_DIR, os.W_OK):
                 alt_log_dir = os.path.expanduser("~") # Fallback to home directory
                 if os.access(alt_log_dir, os.W_OK):
                      log_file_path = os.path.join(alt_log_dir, log_file_name)
                      logging.warning(f"Project directory not writable, attempting to log to: {log_file_path}")
                 else:
                      raise OSError("Log directory not writable.")

            file_handler = logging.FileHandler(log_file_path, mode='a')
            file_handler.setFormatter(logging.Formatter(log_format))
            # Add file handler IN ADDITION to console handler from basicConfig
            root_logger.addHandler(file_handler)
            logging.info(f"Logging configured with level {log_level_str}. Output also sent to: {log_file_path}")

        except Exception as e:
            logging.error(f"Failed to set up file logging to {log_file_path}: {e}", exc_info=True)
            logging.info(f"Logging configured with level {log_level_str}. Output to console only.")
    else:
         logging.info(f"Logging configured with level {log_level_str}. Output to console only.")


    # Set levels for noisy libraries if needed (example)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pyVim").setLevel(logging.INFO) # pyVmomi can be noisy
    logging.getLogger("pyVmomi").setLevel(logging.INFO)
