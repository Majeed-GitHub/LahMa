import pytest
import os
import yaml
from unittest.mock import patch, mock_open

# Import the functions/classes to test from core.config
# Adjust path if necessary, but usually Python path handles this
from core.config import load_config, find_config_file, DEFAULT_CONFIG_PATH, CONFIG_DIR
from core.exceptions import ConfigError

# --- Fixtures (Helper functions/data for tests) ---


@pytest.fixture(scope="function")  # Re-run for each test function using it
def mock_config_files(tmp_path):
    """Creates temporary dummy config files for testing."""
    # tmp_path is a unique temporary directory provided by pytest
    config_dir = tmp_path / CONFIG_DIR  # Use CONFIG_DIR constant from core.config
    config_dir.mkdir()

    # Create a dummy example config
    example_path = config_dir / "config.example.yaml"
    example_content = {
        "logging": {"level": "INFO"},
        "web_fuzzer": {"target_url": "http://example.com"},
        "openai": {"model": "gpt-test"},
    }
    with open(example_path, "w") as f:
        yaml.dump(example_content, f)

    # Create a dummy actual config
    actual_path = config_dir / "config.yaml"
    actual_content = {
        "logging": {"level": "DEBUG", "file": "test.log"},
        "web_fuzzer": {"target_url": "http://actual-test.com"},
        "esxi_tester": {"targets": ["10.0.0.1"]},
    }
    with open(actual_path, "w") as f:
        yaml.dump(actual_content, f)

    # Create a dummy specific config
    specific_path = tmp_path / "specific_config.yaml"
    specific_content = {
        "logging": {"level": "WARNING"},
        "openai": {"api_key": "specific_key"},
    }
    with open(specific_path, "w") as f:
        yaml.dump(specific_content, f)

    # Create an invalid yaml file
    invalid_yaml_path = config_dir / "invalid.yaml"
    invalid_yaml_path.write_text(
        "logging: level: DEBUG\nlogging: level: INFO"
    )  # Duplicate key

    # Return paths for use in tests
    return {
        "tmp_path": tmp_path,  # Base temp directory for this test run
        "config_dir": config_dir,  # Path to the created config subdir
        "example": example_path,  # Path to example config
        "actual": actual_path,  # Path to default config
        "specific": specific_path,  # Path to specific config
        "invalid": invalid_yaml_path,  # Path to invalid config
    }


# --- Test Cases ---


def test_find_config_specific_path_exists(mock_config_files):
    """Test finding config when a specific valid path is given."""
    # Don't need to change directory if we pass absolute path from fixture
    # os.chdir(mock_config_files["tmp_path"])
    found_path = find_config_file(str(mock_config_files["specific"]))
    assert found_path == str(
        mock_config_files["specific"]
    )  # Should return the same absolute path


def test_find_config_specific_path_missing():
    """Test finding config when a specific path is given but file doesn't exist."""
    with pytest.raises(ConfigError, match="does not exist"):
        find_config_file("/path/to/nonexistent/config.yaml")


def test_find_config_default_path_exists(mock_config_files):
    """Test finding config uses default path (config/config.yaml) if it exists."""
    # Change working dir to simulate running from project root relative to temp dir
    os.chdir(mock_config_files["tmp_path"])
    expected_relative_default = os.path.join(
        CONFIG_DIR, "config.yaml"
    )  # Expect relative path
    found_path = find_config_file(None)  # No arg provided
    assert found_path == expected_relative_default


def test_find_config_fallback_to_example(mock_config_files):
    """Test finding config falls back to example if default is missing."""
    os.chdir(mock_config_files["tmp_path"])
    os.remove(mock_config_files["actual"])  # Remove the default config.yaml
    expected_relative_example = os.path.join(
        CONFIG_DIR, "config.example.yaml"
    )  # Expect relative path
    found_path = find_config_file(None)
    assert found_path == expected_relative_example


def test_find_config_no_files_found(mock_config_files):
    """Test finding config returns None if no default or example exists."""
    os.chdir(mock_config_files["tmp_path"])
    os.remove(mock_config_files["actual"])
    os.remove(mock_config_files["example"])
    found_path = find_config_file(None)
    assert found_path is None


def test_load_config_uses_default(mock_config_files):
    """Test loading config uses config.yaml when available."""
    os.chdir(mock_config_files["tmp_path"])
    config = load_config(None)  # Load default
    # Check values from default config file
    assert config["logging"]["level"] == "DEBUG"
    assert config["web_fuzzer"]["target_url"] == "http://actual-test.com"
    assert config["esxi_tester"]["targets"] == ["10.0.0.1"]
    # Check that defaults were added for sections NOT in the file
    assert "openai" in config
    assert config["openai"]["model"] == "gpt-3.5-turbo"  # Default value
    assert "api_key" not in config["openai"]  # Default doesn't add a key


def test_load_config_uses_specific_path(mock_config_files):
    """Test loading config uses the file specified in the argument."""
    # No need to change dir when providing absolute path
    # os.chdir(mock_config_files["tmp_path"])
    config = load_config(str(mock_config_files["specific"]))
    # Check values from specific config file
    assert config["logging"]["level"] == "WARNING"
    assert config["openai"]["api_key"] == "specific_key"
    # Check defaults added for missing sections
    assert config["web_fuzzer"]["target_url"] is None  # Default value
    assert config["esxi_tester"]["targets"] == []  # Default value


def test_load_config_fallback_and_defaults(mock_config_files):
    """Test loading config falls back to example and adds defaults."""
    os.chdir(mock_config_files["tmp_path"])
    os.remove(mock_config_files["actual"])  # Remove config.yaml
    config = load_config(None)  # Load default (will fallback to example)
    # Check values from example config file
    assert config["logging"]["level"] == "INFO"
    assert config["web_fuzzer"]["target_url"] == "http://example.com"
    assert config["openai"]["model"] == "gpt-test"
    # Check default added for sections missing from example
    assert config["esxi_tester"]["targets"] == []  # Default value


def test_load_config_no_file_uses_defaults(mock_config_files):
    """Test loading config uses only defaults when no file is found."""
    os.chdir(mock_config_files["tmp_path"])
    os.remove(mock_config_files["actual"])
    os.remove(mock_config_files["example"])
    config = load_config(None)
    # Check all sections have default values
    assert config["logging"]["level"] == "INFO"
    assert config["openai"]["model"] == "gpt-3.5-turbo"
    assert "api_key" not in config["openai"]
    assert config["esxi_tester"]["targets"] == []
    assert config["web_fuzzer"]["target_url"] is None
    assert config["tor"]["enabled"] is False


def test_load_config_env_var_override(mock_config_files):
    """Test environment variable overrides config file for OpenAI key."""
    # Don't need to change dir, can load specific file directly
    # os.chdir(mock_config_files["tmp_path"])
    # Set environment variable
    test_key = "env_var_key_123"
    # Use patch.dict to temporarily modify os.environ for this test only
    with patch.dict(os.environ, {"OPENAI_API_KEY": test_key}, clear=True):
        # Load specific config which also has an 'openai.api_key'
        config = load_config(str(mock_config_files["specific"]))
        # Env var should take precedence over the key in specific_config.yaml
        assert config["openai"]["api_key"] == test_key
        # Ensure other values from file are still loaded
        assert config["logging"]["level"] == "WARNING"


def test_load_config_invalid_yaml(mock_config_files):
    """Test loading config raises error for invalid YAML."""
    # Don't need to change dir
    # os.chdir(mock_config_files["tmp_path"])
    with pytest.raises(ConfigError, match="Invalid YAML syntax"):
        load_config(str(mock_config_files["invalid"]))
