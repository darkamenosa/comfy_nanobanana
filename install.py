import subprocess
import sys
import os

def install_requirements():
    """Install required packages for comfy_nanobanana."""
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")

    if os.path.exists(requirements_path):
        print("[comfy_nanobanana] Installing requirements...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_path
        ])
        print("[comfy_nanobanana] Requirements installed successfully.")
    else:
        # Fallback: install google-genai directly
        print("[comfy_nanobanana] Installing google-genai...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "google-genai>=1.62.0"
        ])
        print("[comfy_nanobanana] google-genai installed successfully.")

if __name__ == "__main__":
    install_requirements()
