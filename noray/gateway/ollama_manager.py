import os
import sys
import subprocess
import httpx
from typing import Optional
from noray.gateway.hardware_detector import get_hardware_info, recommend_local_model

OLLAMA_API_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def is_ollama_installed() -> bool:
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def install_ollama():
    """Attempts to install Ollama automatically if missing."""
    import platform
    os_name = platform.system()
    
    print("Ollama is not installed. Attempting automatic installation...")
    try:
        if os_name == "Windows":
            print("Please download and install Ollama from https://ollama.com/download/windows")
            sys.exit(1)
        elif os_name == "Darwin":
            # macOS
            subprocess.run(["curl", "-fsSL", "https://ollama.com/install.sh", "-o", "install.sh"], check=True)
            subprocess.run(["sh", "install.sh"], check=True)
        elif os_name == "Linux":
            subprocess.run(["curl", "-fsSL", "https://ollama.com/install.sh", "-o", "install.sh"], check=True)
            subprocess.run(["sh", "install.sh"], check=True)
        print("Ollama installed successfully.")
    except Exception as e:
        print(f"Failed to install Ollama automatically: {e}")
        print("Please install it manually from https://ollama.com/download")
        sys.exit(1)

def pull_model(model_name: str):
    """Pulls a model using the Ollama CLI."""
    print(f"Downloading model: {model_name} (this may take a while...)")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"✓ Model {model_name} downloaded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to download model {model_name}: {e}")

def verify_and_setup_local_ai():
    if not is_ollama_installed():
        install_ollama()
        
    hw = get_hardware_info()
    recommended_model = recommend_local_model(hw)
    
    print(f"Hardware Detected: {hw['ram_gb']}GB RAM, OS: {hw['os']}")
    print(f"Selected Local LLM: {recommended_model}")
    
    pull_model(recommended_model)
    
    # Check embeddings model (e.g. nomic-embed-text)
    embed_model = "nomic-embed-text"
    print(f"Ensuring local embedding model ({embed_model}) is available via Ollama...")
    pull_model(embed_model)

if __name__ == "__main__":
    verify_and_setup_local_ai()
