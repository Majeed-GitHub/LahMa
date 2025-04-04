# Project LahMa 🚀

A modular security toolkit designed for authorized penetration testing, security research, and educational purposes. It integrates various tools and techniques, including AI-powered elements, vulnerability checking, and web application fuzzing.

**⚠️ Warning:** This tool includes modules capable of performing actions that could be harmful if misused. Use responsibly and **only** on systems you have explicit, written authorization to test. Refer to the `DISCLAIMER.md` file before use. The developers assume no liability for misuse.

## Features (Planned/In Development)

*   **AI-Powered Honeypot Module:** Dynamically generate decoy content.
*   **ESXi Assessment Module:** Check ESXi hosts for known vulnerabilities (starting with safe checks).
*   **Web Fuzzer:** Integrate tools like Nuclei for web application scanning.
*   **Modular Core:** Easily extendable with new modules.
*   **Configuration Management:** Load settings from YAML files / environment variables.
*   **Standardized Logging:** Consistent logging across modules.

## Installation

1.  **Clone the repository:**
    ```bash
    # Replace with your repo URL later if you push to GitHub/GitLab etc.
    # git clone https://github.com/yourusername/LahMa.git
    # cd LahMa
    ```
2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv # Or just python -m venv venv
    ```
3.  **Activate the environment:**
    *   Linux/macOS: `source venv/bin/activate`
    *   Windows: `venv\Scripts\activate`
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    # For development (testing, linting):
    pip install -r requirements-dev.txt
    ```
5.  **External Tools:** Some modules (like the Web Fuzzer) require external tools (e.g., Nuclei) to be installed separately and available in your system's PATH.

## Usage

1.  **Configuration:** Copy `config/config.example.yaml` to `config/config.yaml` and edit it according to your needs. Pay special attention to API keys and target specifications. **Do not commit `config.yaml`**.
2.  **Run LahMa:**
    ```bash
    # Show help
    python lahma.py --help

    # Run a specific module (using config/config.yaml by default if it exists)
    python lahma.py --mode fuzz
    python lahma.py --mode esxi
    python lahma.py --mode honeypot

    # Specify a different config file
    python lahma.py --mode fuzz --config /path/to/your/other_config.yaml
    ```

## Contributing

Contributions are welcome! Please read `CONTRIBUTING.md` for guidelines on reporting bugs, proposing features, submitting pull requests, and security reporting.

## License

This project is licensed under the AGPL-3.0 License - see the `LICENSE` file for details.

## Disclaimer

Usage of LahMa is subject to the terms outlined in `DISCLAIMER.md`. Ensure you read and understand it before using the tool.
