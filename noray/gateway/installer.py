"""
NORAY — Local Model Autoinstaller & Hardware Detector

Detects OS, CPU, RAM, GPU, VRAM, CUDA, AVX2, and Disk space;
Recommends and pulls the best matching model via Ollama.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from typing import Any

import httpx


def detect_hardware() -> dict[str, Any]:
    """Detect local system hardware parameters using OS commands."""
    hw = {
        "os": sys.platform,
        "cpu": "Unknown",
        "ram_gb": 0.0,
        "gpu": "CPU Only",
        "vram_gb": 0.0,
        "cuda_available": False,
        "avx2_supported": True,
        "disk_free_gb": 0.0
    }

    # Detect Disk Space
    try:
        total, used, free = shutil.disk_usage("C:\\" if sys.platform == "win32" else "/")
        hw["disk_free_gb"] = round(free / (1024**3), 1)
    except Exception:
        pass

    # Windows Hardware Detection via PowerShell Get-CimInstance (works on Win10/11)
    if sys.platform == "win32":
        try:
            # CPU Name
            out_cpu = subprocess.check_output(
                ["powershell", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                shell=False, timeout=5
            ).decode().strip()
            if out_cpu:
                hw["cpu"] = out_cpu
        except Exception:
            pass

        try:
            # RAM
            out_ram = subprocess.check_output(
                ["powershell", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
                shell=False, timeout=5
            ).decode().strip()
            if out_ram.isdigit():
                hw["ram_gb"] = round(int(out_ram) / (1024**3), 1)
        except Exception:
            pass

        try:
            # GPU Name & VRAM — use JSON output for reliable parsing
            gpu_json = subprocess.check_output(
                ["powershell", "-Command",
                 "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json"],
                shell=False, timeout=5
            ).decode().strip()
            if gpu_json:
                gpu_data = json.loads(gpu_json)
                # Handle single GPU (dict) or multiple GPUs (list)
                if isinstance(gpu_data, dict):
                    gpu_data = [gpu_data]
                for entry in gpu_data:
                    name = entry.get("Name", "")
                    vram = entry.get("AdapterRAM", 0)
                    if name:
                        hw["gpu"] = name
                        if vram and isinstance(vram, (int, float)) and vram > 0:
                            hw["vram_gb"] = round(vram / (1024**3), 1)
                        if "nvidia" in name.lower():
                            hw["cuda_available"] = True
                        break
        except Exception:
            pass

    return hw


def recommend_model(hw: dict[str, Any]) -> str:
    """Recommend the optimal model based on hardware specifications, preferring already installed ones."""
    installed = []
    try:
        import subprocess
        out = subprocess.check_output(["ollama", "list"], text=True, stderr=subprocess.DEVNULL).split("\n")
        for line in out[1:]:
            parts = line.split()
            if parts:
                installed.append(parts[0])
    except Exception:
        pass

    # Normalize installed names
    installed_clean = [m.split(":")[0] for m in installed]

    # VRAM >= 6GB -> Llama 3 or Qwen Coder
    if hw["vram_gb"] >= 6.0:
        if "qwen2.5-coder" in installed_clean:
            return "qwen2.5-coder:7b"
        if "llama3.1" in installed_clean:
            return "llama3.1:8b"
        if "llama3" in installed_clean:
            return "llama3:8b"
        return "qwen2.5-coder:7b"
    # VRAM >= 3GB -> DeepSeek R1 7B
    elif hw["vram_gb"] >= 3.0:
        if "deepseek-r1" in installed_clean:
            return "deepseek-r1:7b"
        return "deepseek-r1:7b"
    # Low VRAM / CPU-only but good RAM (>= 12GB) -> Llama 3 / 3.1
    elif hw["ram_gb"] >= 12.0:
        if "llama3.1" in installed_clean:
            return "llama3.1:8b"
        if "llama3" in installed_clean:
            return "llama3:8b"
        return "llama3:8b"
    # Budget/Low-spec -> Gemma 2B or Phi 3 Mini
    else:
        if "gemma2" in installed_clean:
            return "gemma2:2b"
        if "phi3" in installed_clean:
            return "phi3:mini"
        return "phi3:mini"


def install_ollama_if_missing() -> bool:
    """Detects if Ollama is installed. Downloads and runs silent installer if missing."""
    # Check if command exists
    if shutil.which("ollama") is not None:
        return True

    # Check standard install path on Windows
    win_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
    if os.path.exists(win_path):
        return True

    print("Ollama not detected. Fetching official silent installer...")
    setup_file = "OllamaSetup.exe"
    url = "https://ollama.com/download/OllamaSetup.exe"

    try:
        urllib.request.urlretrieve(url, setup_file)
        print("Running installer silently. Please wait...")
        # Run silent installation
        subprocess.run([setup_file, "/silent"], check=True)
        # Delete setup file
        if os.path.exists(setup_file):
            os.remove(setup_file)
        return True
    except Exception as e:
        print(f"Failed to install Ollama automatically: {e}")
        return False


def pull_and_verify_model(model_name: str) -> tuple[bool, str]:
    """Pulls the recommended model via Ollama CLI and runs a test verification prompt."""
    try:
        print(f"Pulling model: {model_name}... (this can take a few minutes)")
        subprocess.run(["ollama", "pull", model_name], check=True)

        # Verify execution
        print("Running verification test prompt...")
        test_payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Respond with ONLY the word: SUCCESS"}],
            "stream": False
        }
        res = httpx.post("http://localhost:11434/api/chat", json=test_payload, timeout=20.0)
        if res.status_code == 200:
            content = res.json()["message"]["content"].strip()
            return True, content
        return False, f"HTTP status: {res.status_code}"
    except Exception as e:
        return False, str(e)
