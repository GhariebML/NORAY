import platform
from typing import Any


def get_hardware_info() -> dict[str, Any]:
    """Detects system hardware for optimal LLM selection."""
    info: dict[str, Any] = {
        "os": platform.system(),
        "cpu_count": 1,
        "ram_gb": 1.0,
        "gpu_available": False,
        "gpu_vendor": None,
        "vram_gb": 0.0,
        "metal_available": False,
    }

    try:
        import psutil
        info["cpu_count"] = psutil.cpu_count(logical=True) or 1
        info["ram_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except ImportError:
        pass

    if info["os"] == "Darwin" and platform.machine() == "arm64":
        info["gpu_available"] = True
        info["metal_available"] = True
        info["gpu_vendor"] = "Apple"
        info["vram_gb"] = info["ram_gb"]
    else:
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                info["gpu_available"] = True
                info["gpu_vendor"] = "NVIDIA"
                info["vram_gb"] = round(gpu.memoryTotal / 1024, 2)
        except (ImportError, Exception):
            pass

    return info


def recommend_local_model(hw_info: dict[str, Any]) -> str:
    """Recommends the best local LLM based on hardware constraints."""
    ram = hw_info["ram_gb"]
    vram = hw_info["vram_gb"]

    if hw_info["gpu_available"] and vram >= 12.0:
        if vram >= 24.0:
            return "qwen2.5:14b"
        return "qwen2.5:7b"

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
