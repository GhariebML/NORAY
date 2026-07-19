import os
import platform
import psutil
from typing import Dict, Any

try:
    import GPUtil
except ImportError:
    GPUtil = None

def get_hardware_info() -> Dict[str, Any]:
    """Detects system hardware for optimal LLM selection."""
    info = {
        "os": platform.system(),
        "cpu_count": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "gpu_available": False,
        "gpu_vendor": None,
        "vram_gb": 0.0,
        "metal_available": False
    }

    # Check for Apple Silicon (Metal)
    if info["os"] == "Darwin" and platform.machine() == "arm64":
        info["gpu_available"] = True
        info["metal_available"] = True
        info["gpu_vendor"] = "Apple"
        # Apple shares RAM as VRAM
        info["vram_gb"] = info["ram_gb"]
    
    # Check for NVIDIA GPUs
    elif GPUtil:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            info["gpu_available"] = True
            info["gpu_vendor"] = "NVIDIA"
            info["vram_gb"] = round(gpu.memoryTotal / 1024, 2)

    return info

def recommend_local_model(hw_info: Dict[str, Any]) -> str:
    """Recommends the best local LLM based on hardware constraints."""
    ram = hw_info["ram_gb"]
    vram = hw_info["vram_gb"]
    
    # Priority 1: VRAM for GPU inference
    if hw_info["gpu_available"] and vram >= 12.0:
        if vram >= 24.0:
            return "qwen2.5:14b"
        return "qwen2.5:7b"
        
    # Priority 2: RAM for CPU/Unified Memory inference
    if ram < 16:
        return "qwen2.5:3b"
    elif 16 <= ram < 32:
        return "qwen2.5:7b"
    elif 32 <= ram < 64:
        return "qwen2.5:14b"
    else:
        return "deepseek-r1:14b"

if __name__ == "__main__":
    hw = get_hardware_info()
    print("Detected Hardware:", hw)
    print("Recommended Model:", recommend_local_model(hw))
