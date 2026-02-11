"""
ASR Document Scanner Settings
Configuration management for desktop scanner client
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseSettings, validator

class ScannerSettings(BaseSettings):
    """Configuration settings for ASR Document Scanner"""

    # Basic Settings
    app_name: str = "ASR Document Scanner"
    version: str = "2.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Data Storage
    data_dir: Path = Path.home() / ".asr_scanner"
    queue_db_path: Optional[Path] = None
    temp_dir: Optional[Path] = None

    # Server Connection
    api_key: Optional[str] = None
    server_discovery_enabled: bool = True
    server_discovery_timeout: int = 10  # seconds
    auto_connect_servers: bool = True
    heartbeat_interval: int = 30  # seconds

    # Upload Settings
    max_file_size_mb: int = 50
    supported_formats: List[str] = ["pdf", "jpg", "jpeg", "png", "tiff", "gif"]
    batch_upload_size: int = 5
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds

    # Scanner Hardware
    scanner_enabled: bool = True
    scanner_resolution: int = 300  # DPI
    scanner_color_mode: str = "color"  # color, grayscale, black_white
    scanner_format: str = "pdf"
    auto_scan: bool = False

    # GUI Settings
    window_width: int = 1000
    window_height: int = 700
    theme: str = "default"  # default, dark
    show_notifications: bool = True
    auto_minimize_to_tray: bool = False

    # File Monitoring
    watch_folders: List[str] = []
    watch_folder_enabled: bool = False
    auto_upload_from_watch: bool = False

    # Offline Mode
    offline_mode: bool = False
    offline_queue_max_size: int = 1000
    offline_retention_days: int = 7

    # Network Settings
    connection_timeout: int = 30
    read_timeout: int = 60
    max_connections: int = 10

    @validator('data_dir')
    def validate_data_dir(cls, v):
        """Ensure data directory exists"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    @validator('queue_db_path', pre=True, always=True)
    def set_queue_db_path(cls, v, values):
        """Set default queue database path"""
        if v is None:
            data_dir = values.get('data_dir', Path.home() / ".asr_scanner")
            return data_dir / "upload_queue.db"
        return v

    @validator('temp_dir', pre=True, always=True)
    def set_temp_dir(cls, v, values):
        """Set default temp directory"""
        if v is None:
            data_dir = values.get('data_dir', Path.home() / ".asr_scanner")
            temp_path = data_dir / "temp"
            temp_path.mkdir(parents=True, exist_ok=True)
            return temp_path
        return v

    @validator('supported_formats')
    def normalize_formats(cls, v):
        """Normalize file format extensions"""
        return [fmt.lower().lstrip('.') for fmt in v]

    @validator('max_file_size_mb')
    def validate_file_size(cls, v):
        """Validate maximum file size"""
        if v <= 0:
            raise ValueError("Max file size must be positive")
        if v > 100:
            raise ValueError("Max file size too large (max 100MB)")
        return v

    @validator('scanner_resolution')
    def validate_scanner_resolution(cls, v):
        """Validate scanner resolution"""
        valid_resolutions = [150, 200, 300, 400, 600, 1200]
        if v not in valid_resolutions:
            raise ValueError(f"Scanner resolution must be one of: {valid_resolutions}")
        return v

    @validator('scanner_color_mode')
    def validate_color_mode(cls, v):
        """Validate scanner color mode"""
        valid_modes = ["color", "grayscale", "black_white"]
        if v not in valid_modes:
            raise ValueError(f"Scanner color mode must be one of: {valid_modes}")
        return v

    def get_upload_config(self) -> Dict[str, Any]:
        """Get upload-related configuration"""
        return {
            "max_file_size_mb": self.max_file_size_mb,
            "supported_formats": self.supported_formats,
            "batch_size": self.batch_upload_size,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "connection_timeout": self.connection_timeout,
            "read_timeout": self.read_timeout
        }

    def get_scanner_config(self) -> Dict[str, Any]:
        """Get scanner hardware configuration"""
        return {
            "enabled": self.scanner_enabled,
            "resolution": self.scanner_resolution,
            "color_mode": self.scanner_color_mode,
            "format": self.scanner_format,
            "auto_scan": self.auto_scan
        }

    def get_gui_config(self) -> Dict[str, Any]:
        """Get GUI configuration"""
        return {
            "window_width": self.window_width,
            "window_height": self.window_height,
            "theme": self.theme,
            "show_notifications": self.show_notifications,
            "auto_minimize_to_tray": self.auto_minimize_to_tray
        }

    def save_to_file(self, config_path: Optional[Path] = None) -> None:
        """Save current settings to configuration file"""
        if config_path is None:
            config_path = self.data_dir / "scanner_config.json"

        config_data = self.dict()

        # Convert Path objects to strings for JSON serialization
        for key, value in config_data.items():
            if isinstance(value, Path):
                config_data[key] = str(value)

        import json
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)

    @classmethod
    def load_from_file(cls, config_path: Path) -> 'ScannerSettings':
        """Load settings from configuration file"""
        import json
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        return cls(**config_data)

    class Config:
        env_prefix = "ASR_SCANNER_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = 'utf-8'


# Create global scanner settings instance
scanner_settings = ScannerSettings()