import logging
import subprocess
import shlex
import os
from typing import Dict, Any, Optional, Union  # Added Union

# Assuming core utilities are accessible via the Python path
# Adjust import path if needed based on how you run/install
try:
    # Import only needed exceptions directly
    from core.exceptions import WebFuzzerError, ConfigError, EnvironmentError
except ImportError:
    # If core exceptions can't be imported, the program likely can't run anyway.
    # Let the ImportError propagate or handle it more gracefully if needed later.
    print(
        "CRITICAL ERROR: Cannot import core exceptions from web_fuzzer. Check project structure/PYTHONPATH."
    )
    raise  # Re-raise the ImportError


logger = logging.getLogger(__name__)  # Gets logger named "modules.web_fuzzer"


def check_nuclei_installed() -> bool:
    """Checks if the 'nuclei' command is accessible in the PATH."""
    try:
        # Use subprocess.run to check, suppress output
        subprocess.run(
            ["nuclei", "-version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        logger.debug("Nuclei installation confirmed.")
        return True
    except FileNotFoundError:
        logger.error(
            "Nuclei command not found. Please install Nuclei and ensure it's in your system PATH."
        )
        return False
    except subprocess.CalledProcessError as e:
        logger.warning(
            f"Nuclei command found, but '-version' exited with error: {e.stderr}"
        )
        # Could still be usable, but maybe misconfigured? Treat as installed for now.
        return True
    except subprocess.TimeoutExpired:
        logger.error("Checking Nuclei version timed out.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while checking for Nuclei: {e}")
        return False


# Optional type hints are fine
def run_nuclei(
    target_url: str,
    templates_path: Optional[str],
    extra_flags_str: str,
    process_timeout: int,
) -> bool:
    """
    Runs the Nuclei scanner against a target URL using subprocess.

    Args:
        target_url: The URL to scan.
        templates_path: Optional path/glob for Nuclei templates (-t flag).
        extra_flags_str: String of additional Nuclei command-line flags.
        process_timeout: Timeout in seconds for the Nuclei process.

    Returns:
        True if Nuclei ran successfully (exit code 0). Note: Does not indicate findings.

    Raises:
        WebFuzzerError: If Nuclei fails to execute (e.g., timeout, non-zero exit).
        EnvironmentError: If Nuclei command is not found initially.
    """
    logger.info(f"Preparing to run Nuclei against: {target_url}")
    command = ["nuclei", "-u", target_url]

    if templates_path:
        command.extend(["-t", templates_path])
        logger.info(f"Using Nuclei templates from: {templates_path}")

    if extra_flags_str:
        try:
            extra_args = shlex.split(extra_flags_str)
            command.extend(extra_args)
            logger.info(f"Adding extra Nuclei flags: {extra_args}")
        except ValueError as e:
            logger.error(
                f"Error parsing extra flags '{extra_flags_str}': {e}. Flags ignored."
            )

    safe_command_str = " ".join(shlex.quote(c) for c in command)
    logger.debug(f"Executing Nuclei command: {safe_command_str}")

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=process_timeout,
        )

        if process.stdout:
            logger.info("Nuclei stdout:")
            for line in process.stdout.strip().splitlines():
                logger.info(f"  [NUCLEI_OUT] {line}")
        else:
            logger.info("Nuclei stdout: (empty)")

        if process.stderr:
            logger.info("Nuclei stderr:")
            for line in process.stderr.strip().splitlines():
                logger.info(f"  [NUCLEI_ERR] {line}")
        else:
            logger.info("Nuclei stderr: (empty)")

        if process.returncode != 0:
            logger.error(f"Nuclei exited with non-zero status: {process.returncode}")
            raise WebFuzzerError(
                f"Nuclei process failed with exit code {process.returncode}."
            )
        else:
            logger.info("Nuclei scan process completed successfully (exit code 0).")
            return True

    except FileNotFoundError:
        logger.critical(
            "Nuclei command failed with FileNotFoundError during execution attempt."
        )
        raise EnvironmentError(
            "Nuclei executable not found during execution. Please ensure it is installed and in the system PATH."
        ) from None
    except subprocess.TimeoutExpired:
        logger.error(f"Nuclei scan timed out after {process_timeout} seconds.")
        raise WebFuzzerError(
            f"Nuclei scan process timed out ({process_timeout}s)."
        ) from None
    except Exception as e:
        logger.critical(
            f"An unexpected error occurred while running Nuclei command: {e}",
            exc_info=True,
        )
        raise WebFuzzerError(f"Nuclei execution failed unexpectedly: {e}") from e


# Placeholder for other tools like ParamSpider
def run_paramspider(target_url: str, config: Dict[str, Any]):
    logger.warning("ParamSpider functionality is not yet implemented.")
    pass


# Main entry point function for this module, called by lahma.py
def run(config: Dict[str, Any]):
    """
    Entry point for the Web Fuzzer module. Orchestrates scans.
    """
    logger.info("--- Starting Web Fuzzer Module ---")
    fuzzer_config = config.get("web_fuzzer", {})
    nuclei_config = fuzzer_config.get("nuclei", {})

    target_url = fuzzer_config.get("target_url")
    if not target_url:
        raise ConfigError(
            "Required setting 'web_fuzzer.target_url' is missing in configuration."
        )

    logger.info(f"Target URL: {target_url}")

    # 1. Check for external dependencies (Nuclei)
    if not check_nuclei_installed():
        raise EnvironmentError(
            "Nuclei dependency check failed. Cannot proceed with Nuclei scan."
        )

    # 2. Run ParamSpider (Placeholder)
    # ...

    # 3. Run Nuclei Scan
    logger.info("Proceeding with Nuclei scan...")
    nuclei_success = (
        run_nuclei(  # Directly call run_nuclei; it will raise errors on failure
            target_url=target_url,
            templates_path=nuclei_config.get("templates_path"),
            extra_flags_str=nuclei_config.get("extra_flags", ""),
            process_timeout=nuclei_config.get("process_timeout", 600),
        )
    )

    # This code only runs if run_nuclei returns True (doesn't raise an error)
    if nuclei_success:
        logger.info("Nuclei scan execution completed.")
        # TODO: Add parsing of Nuclei results here (e.g., if -json flag used)

    # 4. Wrap up
    logger.info("--- Web Fuzzer Module Finished ---")
