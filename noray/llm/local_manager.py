import os
import re
import sys
import httpx
import logging
import asyncio
import subprocess
import shutil
from typing import Dict, Any, List

logger = logging.getLogger("noray.llm.local_manager")

class LocalRuntimeManager:
    """Manages local AI runtime diagnostics, system hardware detection, and Ollama models."""

    def __init__(self):
        self.ollama_url = "http://localhost:11434"

    def get_hardware_info(self) -> Dict[str, Any]:
        """Detect system CPU, RAM, and GPU/VRAM capacity."""
        info = {
            "cpu": "Unknown",
            "ram_gb": 0.0,
            "gpu": "None",
            "vram_gb": 0.0,
            "supported": True
        }

        try:
            # 1. CPU detection
            if sys.platform == "win32":
                try:
                    cpu_out = subprocess.check_output("wmic cpu get name", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                    lines = [line.strip() for line in cpu_out.split("\n") if line.strip() and "Name" not in line]
                    if lines:
                        info["cpu"] = lines[0]
                except Exception:
                    cpu_out = subprocess.check_output("powershell -Command \"(Get-CimInstance Win32_Processor).Name\"", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                    if cpu_out:
                        info["cpu"] = cpu_out
            else:
                info["cpu"] = "Generic CPU"
        except Exception as e:
            logger.warning(f"Failed to detect CPU: {e}")

        try:
            # 2. RAM detection
            if sys.platform == "win32":
                try:
                    mem_out = subprocess.check_output("wmic ComputerSystem get TotalPhysicalMemory", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                    lines = [line.strip() for line in mem_out.split("\n") if line.strip() and "TotalPhysicalMemory" not in line]
                    if lines:
                        bytes_val = int(lines[0])
                        info["ram_gb"] = round(bytes_val / (1024 ** 3), 2)
                except Exception:
                    mem_out = subprocess.check_output("powershell -Command \"(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum\"", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                    if mem_out:
                        bytes_val = int(mem_out)
                        info["ram_gb"] = round(bytes_val / (1024 ** 3), 2)
        except Exception as e:
            logger.warning(f"Failed to detect RAM: {e}")

        try:
            # 3. GPU / VRAM detection (NVIDIA nvidia-smi check)
            if shutil.which("nvidia-smi"):
                out = subprocess.check_output("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                parts = out.split(",")
                if len(parts) >= 2:
                    info["gpu"] = parts[0].strip()
                    mibs = int(parts[1].strip())
                    info["vram_gb"] = round(mibs / 1024, 2)
            else:
                # Fallback to Windows VideoController checking if nvidia-smi is missing
                if sys.platform == "win32":
                    try:
                        gpu_out = subprocess.check_output("wmic path win32_VideoController get Name,AdapterRAM", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                        lines = [line.strip() for line in gpu_out.split("\n") if line.strip() and "AdapterRAM" not in line]
                        # Select first line that matches non-zero AdapterRAM or has NVIDIA/AMD
                        for line in lines:
                            match = re.match(r"(\d+)\s+(.+)", line)
                            if match:
                                ram_bytes = int(match.group(1))
                                name = match.group(2)
                                if "nvidia" in name.lower() or "amd" in name.lower() or ram_bytes > 0:
                                    info["gpu"] = name
                                    info["vram_gb"] = round(ram_bytes / (1024 ** 3), 2)
                                    break
                    except Exception:
                        gpu_out = subprocess.check_output("powershell -Command \"Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json\"", shell=True, stderr=subprocess.DEVNULL).decode().strip()
                        if gpu_out:
                            # Simple parsing of json structure
                            import json
                            gpu_data = json.loads(gpu_out)
                            if isinstance(gpu_data, dict):
                                gpu_data = [gpu_data]
                            for item in gpu_data:
                                name = item.get("Name", "")
                                ram_bytes = item.get("AdapterRAM", 0) or 0
                                if "nvidia" in name.lower() or "amd" in name.lower() or ram_bytes > 0:
                                    info["gpu"] = name
                                    info["vram_gb"] = round(ram_bytes / (1024 ** 3), 2)
                                    break
        except Exception as e:
            logger.warning(f"Failed to detect GPU: {e}")

        return info

    def get_model_recommendations(self) -> List[str]:
        """Suggest appropriate Ollama models depending on available hardware capacity."""
        hardware = self.get_hardware_info()
        vram = hardware["vram_gb"]
        ram = hardware["ram_gb"]

        recommended = ["nomic-embed-text"] # always recommend embeddings

        if vram >= 6.0 or ram >= 16.0:
            recommended.append("qwen2.5:7b")
            recommended.append("llama3.1:8b")
            recommended.append("deepseek-r1:8b")
        else:
            recommended.append("qwen2.5:1.5b") # light model recommendation for low resources
            recommended.append("llama3.2:1b")
        return recommended

    async def is_ollama_running(self) -> bool:
        """Check if Ollama local server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(self.ollama_url)
                return res.status_code == 200
        except Exception:
            return False

    async def ensure_ollama_started(self) -> bool:
        """Start Ollama background process if it is not already running."""
        if await self.is_ollama_running():
            return True

        logger.info("Attempting to start local Ollama server...")
        # Check if Ollama command exists in path
        if not shutil.which("ollama"):
            logger.error("Ollama CLI is not installed on this system.")
            return False

        try:
            if sys.platform == "win32":
                subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait up to 5 seconds for Ollama to spin up
            for _ in range(10):
                await asyncio.sleep(0.5)
                if await self.is_ollama_running():
                    logger.info("Ollama server started successfully.")
                    return True
        except Exception as e:
            logger.error(f"Failed to start Ollama subprocess: {e}")
        return False

    async def get_downloaded_models(self) -> List[Dict[str, Any]]:
        """Retrieve list of locally pulled models from Ollama."""
        if not await self.is_ollama_running():
            return []

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.ollama_url}/api/tags")
                if res.status_code == 200:
                    models_data = res.json().get("models", [])
                    return [
                        {
                            "name": m.get("name"),
                            "size_bytes": m.get("size"),
                            "family": m.get("details", {}).get("family"),
                            "format": m.get("details", {}).get("format")
                        } for m in models_data
                    ]
        except Exception as e:
            logger.error(f"Failed to fetch downloaded models: {e}")
        return []

    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from the Ollama library registry."""
        if not await self.ensure_ollama_started():
            return False

        logger.info(f"Starting programmatic pull for model: {model_name}")
        url = f"{self.ollama_url}/api/pull"
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, json={"name": model_name}) as response:
                    if response.status_code != 200:
                        return False
                    async for line in response.aiter_lines():
                        pass # consume stream lines
            logger.info(f"Finished pulling model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model '{model_name}': {e}")
            return False

# Global runtime manager instance
local_runtime = LocalRuntimeManager()
