"""
GPU detection and automatic configuration for Ollama batch processing.
"""

import logging
import subprocess
import platform
from typing import Dict, Any, Optional
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class GPUDetector:
    """Detects GPU capabilities and recommends optimal batch settings."""
    
    # VRAM thresholds (GB)
    TIERS = {
        "ultra_high_end": 40,  # 48GB+ (A100, RTX 5090)
        "high_end": 20,        # 24GB+ (RTX 4090, H100)
        "upper_mid_range": 14, # 16GB+ (RTX 3080, 5080)
        "mid_range": 10,       # 12GB+ (RTX 3060, 4060)
        "low_end": 5,          # 6GB+ (GTX 1660, RTX 2060)
        "cpu": 0               # CPU fallback
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize GPU detector.
        
        Args:
            config_path: Path to llm_config.yaml (default: configs/llm_config.yaml)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "configs" / "llm_config.yaml"
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Dict[str, Any]]:
        """Load LLM configuration from YAML."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_path}: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Dict[str, Any]]:
        """Fallback configuration if YAML not found."""
        return {
            "ultra_high_end": {"batch_size": 32, "max_concurrent": 16, "model": "qwen2.5:14b"},
            "high_end": {"batch_size": 16, "max_concurrent": 8, "model": "qwen2.5:14b"},
            "upper_mid_range": {"batch_size": 12, "max_concurrent": 6, "model": "qwen2.5:7b"},
            "mid_range": {"batch_size": 8, "max_concurrent": 4, "model": "qwen2.5:7b"},
            "low_end": {"batch_size": 4, "max_concurrent": 2, "model": "qwen2.5:3b"},
            "cpu": {"batch_size": 2, "max_concurrent": 1, "model": "qwen2.5:3b"}
        }
    
    def detect_vram(self) -> Optional[float]:
        """
        Detect available VRAM in GB.
        
        Returns:
            VRAM in GB, or None if no GPU detected
        """
        system = platform.system()
        
        if system == "Windows":
            return self._detect_vram_windows()
        elif system in ["Linux", "Darwin"]:  # macOS uses Darwin
            return self._detect_vram_unix()
        else:
            logger.warning(f"Unsupported OS for GPU detection: {system}")
            return None
    
    def _detect_vram_windows(self) -> Optional[float]:
        """Detect VRAM on Windows via nvidia-smi."""
        try:
            # Try nvidia-smi first
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                vram_mb = float(result.stdout.strip().split('\n')[0])
                vram_gb = vram_mb / 1024
                logger.info(f"Detected NVIDIA GPU with {vram_gb:.1f}GB VRAM")
                return vram_gb
            
        except (subprocess.SubprocessError, FileNotFoundError, ValueError) as e:
            logger.debug(f"nvidia-smi not available: {e}")
        
        # Try AMD ROCm (rocm-smi)
        try:
            result = subprocess.run(
                ["rocm-smi", "--showmeminfo", "vram"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse ROCm output (implementation varies by version)
                logger.info("Detected AMD GPU (manual configuration recommended)")
                return None  # ROCm parsing is complex, fallback to manual
                
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.debug(f"rocm-smi not available: {e}")
        
        logger.warning("No GPU detected, falling back to CPU mode")
        return None
    
    def _detect_vram_unix(self) -> Optional[float]:
        """Detect VRAM on Linux/macOS."""
        # Same logic as Windows (nvidia-smi is cross-platform)
        return self._detect_vram_windows()
    
    def get_tier(self, vram_gb: Optional[float]) -> str:
        """
        Determine hardware tier based on VRAM.
        
        Args:
            vram_gb: VRAM in GB (None for CPU)
        
        Returns:
            Tier name (e.g., "high_end", "cpu")
        """
        if vram_gb is None:
            return "cpu"
        
        for tier, threshold in self.TIERS.items():
            if vram_gb >= threshold:
                return tier
        
        return "cpu"  # Fallback
    
    def get_config(self, tier: Optional[str] = None, vram_gb: Optional[float] = None) -> Dict[str, Any]:
        """
        Get optimal configuration for detected hardware.
        
        Args:
            tier: Force specific tier (optional)
            vram_gb: Override VRAM detection (optional)
        
        Returns:
            Configuration dict with batch_size, max_concurrent, model
        """
        if tier is None:
            if vram_gb is None:
                vram_gb = self.detect_vram()
            tier = self.get_tier(vram_gb)
        
        config = self.config.get(tier, self.config["cpu"])
        logger.info(f"Using '{tier}' configuration: {config}")
        
        return config
    
    def auto_configure(self) -> Dict[str, Any]:
        """
        Automatically detect GPU and return optimal configuration.
        
        Returns:
            Configuration dict ready for LLMClassifier
        """
        vram_gb = self.detect_vram()
        
        if vram_gb:
            logger.info(f"🎮 GPU detected: {vram_gb:.1f}GB VRAM")
        else:
            logger.info("🖥️  No GPU detected, using CPU mode")
        
        return self.get_config(vram_gb=vram_gb)


# Singleton instance
_detector: Optional[GPUDetector] = None

def get_detector() -> GPUDetector:
    """Get global GPU detector instance."""
    global _detector
    if _detector is None:
        _detector = GPUDetector()
    return _detector