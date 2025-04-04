import logging
import ssl
import socket
from typing import Dict, Any, List, Tuple

# Import pyVmomi libraries
try:
    from pyVim import connect
    from pyVmomi import vim, vmodl
    PYVMOMI_AVAILABLE = True
except ImportError:
    # Handle case where pyVmomi might be missing, although it's in requirements.txt
    PYVMOMI_AVAILABLE = False
    # Define dummy classes/objects if needed for the script to load without pyVmomi
    class vim: pass
    class vmodl:
         class RuntimeFault(Exception): pass # Base exception
         class MethodFault(RuntimeFault): pass
         class VimFault(RuntimeFault): pass

    class connect:
         @staticmethod
         def SmartConnect(host, port, user, pwd, sslContext): pass
         @staticmethod
         def SmartConnectNoSSL(host, port): pass
         @staticmethod
         def Disconnect(si): pass

# Import LahMa specific exceptions
try:
     from core.exceptions import EsxiTesterError, ConfigError, EnvironmentError
except ImportError:
     print("ERROR: Cannot import core exceptions from esxi_tester.")
     class EsxiTesterError(Exception): pass
     class ConfigError(Exception): pass
     class EnvironmentError(Exception): pass


logger = logging.getLogger(__name__) # Gets logger named "modules.esxi_tester"


def check_esxi_target(host: str, port: int, timeout: int) -> Tuple[bool, str]:
    """
    Performs a safe check on a potential ESXi host.

    Attempts to connect using pyVmomi and retrieve basic info.

    Args:
        host: The IP address or hostname of the target.
        port: The port to connect to (usually 443).
        timeout: Connection timeout in seconds.

    Returns:
        A tuple (success: bool, message: str).
        success is True if connection and info retrieval succeeded.
        message provides details (version info or error).
    """
    if not PYVMOMI_AVAILABLE:
        raise EnvironmentError("pyVmomi library is required for the ESXi module but is not installed.")

    logger.info(f"Checking ESXi target: {host}:{port} (Timeout: {timeout}s)")
    service_instance = None
    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout) # Set socket timeout for pyVmomi connection

    # Prepare SSL context - Ignore certificate verification for initial check
    # WARNING: Ignoring SSL verification is insecure for actual operations,
    # but often necessary for initial checks against self-signed certs.
    context = None
    if hasattr(ssl, '_create_unverified_context'):
        context = ssl._create_unverified_context()

    try:
        # Attempt to connect using SmartConnect (handles different API versions)
        # Use dummy credentials as we only need read-only access for basic info
        # If the target requires auth even for basic info, this might fail differently.
        service_instance = connect.SmartConnect(
            host=host,
            port=port,
            user="", # Dummy user
            pwd="",  # Dummy password
            sslContext=context # Ignore SSL cert validation
        )

        if service_instance:
            about_info = service_instance.content.about
            version = about_info.version
            product_name = about_info.fullName
            api_version = about_info.apiVersion
            message = (f"Successfully connected. Product: {product_name}, "
                       f"Version: {version}, API Version: {api_version}")
            logger.info(message)
            return True, message
        else:
            # Should not happen if SmartConnect doesn't raise an error, but defensive check
            message = "Connection attempt returned no service instance."
            logger.warning(message)
            return False, message

    except vmodl.MethodFault as e:
        # Specific VMware errors (e.g., authentication failure if dummy creds not allowed)
        message = f"VMware API error: {e.msg}"
        logger.error(f"Failed to check {host}:{port} - {message}", exc_info=True)
        return False, message
    except (socket.timeout, TimeoutError) as e:
        message = f"Connection timed out after {timeout} seconds."
        logger.warning(f"{message} Target: {host}:{port}")
        return False, message
    except (socket.gaierror, socket.herror) as e:
         message = f"DNS resolution error: {e}"
         logger.error(f"{message} Target: {host}")
         return False, message
    except (ConnectionRefusedError, OSError) as e:
        # Handle cases where port is closed or host is unreachable
        message = f"Connection error: {e}"
        logger.warning(f"{message} Target: {host}:{port}")
        return False, message
    except Exception as e:
        # Catch other unexpected pyVmomi or general errors
        message = f"An unexpected error occurred during connection: {e}"
        logger.error(f"{message} Target: {host}:{port}", exc_info=True)
        return False, message

    finally:
        # Ensure disconnection if connection was successful
        if service_instance:
            try:
                connect.Disconnect(service_instance)
                logger.debug(f"Disconnected from {host}:{port}")
            except Exception as e:
                logger.warning(f"Failed to disconnect from {host}:{port}: {e}", exc_info=True)
        # Restore original socket timeout
        socket.setdefaulttimeout(original_timeout)


# Main entry point function for this module
def run(config: Dict[str, Any]):
    """
    Entry point for the ESXi Tester module. Runs safe checks.
    """
    logger.info("--- Starting ESXi Tester Module ---")
    esxi_config = config.get('esxi_tester', {})
    targets = esxi_config.get('targets', [])
    timeout = esxi_config.get('check_timeout', 10) # Default timeout 10s

    if not targets:
        raise ConfigError("No ESXi targets specified ('esxi_tester.targets' is empty or missing).")

    if not PYVMOMI_AVAILABLE:
         # Check again at module entry point
         raise EnvironmentError("pyVmomi library is required for the ESXi module but is not installed.")

    logger.warning("Executing SAFE checks against configured ESXi targets.")
    logger.warning("Ensure you have AUTHORIZATION before scanning any targets.")

    results = {}
    for target_entry in targets:
        host = str(target_entry) # Basic handling, assumes IP or hostname
        port = 443 # Default ESXi/vCenter HTTPS port

        # Allow specifying port like "hostname:port" (basic parsing)
        if ':' in host:
            try:
                host, port_str = host.split(':', 1)
                port = int(port_str)
            except ValueError:
                logger.error(f"Invalid target format: '{target_entry}'. Skipping.")
                results[target_entry] = (False, f"Invalid format (expected 'host' or 'host:port').")
                continue # Skip to next target

        try:
            success, message = check_esxi_target(host, port, timeout)
            results[target_entry] = (success, message)
        except Exception as e:
            # Catch unexpected errors from the check function itself
            logger.critical(f"Unexpected error while processing target {target_entry}: {e}", exc_info=True)
            results[target_entry] = (False, f"Critical unexpected error: {e}")


    # Log summary of results
    logger.info("--- ESXi Check Results ---")
    successful_checks = 0
    failed_checks = 0
    for target, (success, message) in results.items():
        if success:
            logger.info(f"[+] Target: {target} - SUCCESS: {message}")
            successful_checks += 1
        else:
            logger.warning(f"[-] Target: {target} - FAILED: {message}")
            failed_checks += 1
    logger.info(f"Summary: {successful_checks} successful connection(s), {failed_checks} failed connection/check(s).")

    logger.info("--- ESXi Tester Module Finished ---")
