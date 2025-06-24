#!/usr/bin/env python3
"""
Launch script for the Funes Agent UI.
Run this script to start the Streamlit web interface.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Streamlit UI."""
    app_path = Path(__file__).parent / "app.py"
    
    if not app_path.exists():
        print(f"Error: {app_path} not found")
        sys.exit(1)
    
    print("Starting Funes Agent UI...")
    print("The web interface will open in your browser automatically.")
    print("Press Ctrl+C to stop the server.")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.headless", "false",
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()