"""
NORAY — Local Model Autoinstaller & Hardware Detector Tests
"""

import pytest
from noray.gateway.installer import detect_hardware, recommend_model


def test_hardware_detection_dictionary_structure():
    hw = detect_hardware()
    assert isinstance(hw, dict)
    assert "os" in hw
    assert "cpu" in hw
    assert "ram_gb" in hw
    assert "vram_gb" in hw
    assert "disk_free_gb" in hw


def test_recommend_model_decision_trees():
    from unittest.mock import patch
    with patch("subprocess.check_output", side_effect=Exception("No ollama list")):
        # 1. High-spec GPU config
        hw_high = {
            "ram_gb": 16.0,
            "vram_gb": 8.0
        }
        assert recommend_model(hw_high) == "qwen2.5-coder:7b"
        
        # 2. Medium-spec GPU config
        hw_med = {
            "ram_gb": 16.0,
            "vram_gb": 4.0
        }
        assert recommend_model(hw_med) == "deepseek-r1:7b"
        
        # 3. CPU only but good RAM config
        hw_cpu_high = {
            "ram_gb": 16.0,
            "vram_gb": 0.0
        }
        assert recommend_model(hw_cpu_high) == "llama3:8b"
        
        # 4. Low spec config
        hw_low = {
            "ram_gb": 4.0,
            "vram_gb": 0.0
        }
        assert recommend_model(hw_low) == "phi3:mini"
