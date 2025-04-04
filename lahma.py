#!/usr/bin/env python3
import click
import logging
import sys
import os

# Ensure the core package is importable if running as a script
# (though activating venv usually handles this for installed packages)
# sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.logger import setup_logging
from core.config import load_config, DEFAULT_CONFIG_PATH
from core.exceptions import (
    LahMaError,
    ConfigError,
    ModuleError,
    ApiError,
    EnvironmentError,
)

# --- Module Import Placeholders ---
# We import the run function from each module's __init__.py
# These will be filled in later. For now, create dummy functions if the files don't exist
# or if the run functions aren't defined yet, just to make the CLI runnable.

try:
    from modules.honeypot import run as run_honeypot
except ImportError:

    def run_honeypot(config):
        logging.error("Honeypot module not implemented yet.")


try:
    from modules.esxi_tester import run as run_esxi_tests
except ImportError:

    def run_esxi_tests(config):
        logging.error("ESXi Tester module not implemented yet.")


try:
    from modules.web_fuzzer import run as run_web_fuzzer
except ImportError:

    def run_web_fuzzer(config):
        logging.error("Web Fuzzer module not implemented yet.")


# --- End Module Import Placeholders ---


# Get a logger for the main script itself
logger = logging.getLogger("lahma_cli")


# Define the main command group
@click.group()
@click.version_option(version="0.1.0", prog_name="LahMa")  # Add a version option
@click.option(
    "--config",
    "-c",
    type=click.Path(dir_okay=False),  # File must exist handled by load_config logic
    default=None,  # Let load_config find default if None
    help=f"Path to the configuration file (default: {DEFAULT_CONFIG_PATH} if found).",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default=None,  # Will be merged with config
    help="Override log level from config file.",
)
@click.option(
    "--log-file",
    type=click.Path(dir_okay=False),  # Allow specifying a log file path
    default=None,  # Will be merged with config
    help="Override log file path from config file. Use 'NONE' for console only.",
)
@click.pass_context  # Pass context to subcommands if needed later, good practice
def cli(ctx, config: str | None, log_level: str | None, log_file: str | None):
    """
    🚀 LahMa: Modular Security Toolkit

    Run modules using commands like 'lahma run honeypot'.
    Use --help with a command for module-specific options if added later.
    """
    ctx.ensure_object(
        dict
    )  # Ensure ctx.obj exists for storing shared objects like config

    try:
        # 1. Load Configuration (will raise ConfigError if --config path is bad)
        cfg = load_config(config)
        ctx.obj["CONFIG"] = cfg  # Store loaded config in context

        # 2. Determine effective logging settings (CLI overrides config)
        # Handle explicit "NONE" for log file override
        final_log_file = None if log_file == "NONE" else log_file
        final_log_file = final_log_file or cfg.get("logging", {}).get("file")

        final_log_level = log_level or cfg.get("logging", {}).get("level", "INFO")

        # 3. Setup Logging (MUST happen after config load)
        # Pass the resolved filename, not the path override string
        setup_logging(final_log_level, final_log_file if final_log_file else None)
        logger.info(f"LahMa CLI initialized. Log level: {final_log_level}.")
        if final_log_file and final_log_file != "NONE":
            logger.info(f"Logging to file: {os.path.abspath(final_log_file)}")
        logger.debug("CLI arguments processed.")
        # Avoid logging full config at INFO level if it contains secrets
        logger.debug(f"Loaded configuration object: {cfg}")

    except ConfigError as e:
        # Log configuration errors specifically before exiting
        # Logging might not be fully set up yet if config loading failed early
        # so also print to stderr.
        logger.error(
            f"Configuration Error: {e}", exc_info=False
        )  # Don't need full traceback for simple config errors
        click.echo(f"Error: Configuration failed - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        # Catch unexpected errors during setup
        logger.critical(f"Critical error during CLI initialization: {e}", exc_info=True)
        click.echo(f"Error: Critical initialization failed - {e}", err=True)
        sys.exit(1)


# Define a subcommand group for running modules
@cli.command(name="run")
@click.argument(
    "mode", type=click.Choice(["honeypot", "esxi", "fuzz"], case_sensitive=False)
)
@click.pass_context  # Get config from context
def run_module(ctx, mode: str):
    """Runs the specified LahMa module."""
    cfg = ctx.obj["CONFIG"]  # Retrieve config from context
    logger.info(f"Attempting to run module: {mode}")

    module_map = {
        "honeypot": run_honeypot,
        "esxi": run_esxi_tests,
        "fuzz": run_web_fuzzer,
    }

    run_function = module_map.get(mode)

    if run_function:
        try:
            logger.info(f"Executing {mode} module...")
            run_function(cfg)  # Pass the loaded config to the module's run function
            logger.info(f"Finished execution of {mode} module.")
        except (ModuleError, ApiError, EnvironmentError, ConfigError) as e:
            # Catch specific LahMa errors originating from modules
            logger.error(
                f"Error during '{mode}' module execution: {e}", exc_info=False
            )  # Less verbose logging for known errors
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            # Catch unexpected errors within a module
            logger.critical(
                f"An unexpected critical error occurred in the '{mode}' module: {e}",
                exc_info=True,
            )
            click.echo(f"Error: An unexpected critical error occurred: {e}", err=True)
            sys.exit(1)
    else:
        # This should ideally be caught by click.Choice, but good to have
        logger.error(f"Selected mode '{mode}' does not match any known module.")
        click.echo(f"Error: Invalid mode '{mode}'.", err=True)
        sys.exit(1)


# Entry point for script execution
if __name__ == "__main__":
    # Add a top-level try-except just in case something fails before Click takes over
    try:
        cli(obj={})  # Pass initial empty object for context
    except Exception as e:
        # Fallback logging/printing if error happens extremely early
        print(
            f"FATAL: An unexpected error occurred before CLI could fully initialize: {e}",
            file=sys.stderr,
        )
        # Consider basic logging setup here if needed for very early errors
        sys.exit(1)
