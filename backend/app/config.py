"""Application configuration settings for RoadGuard AI backend."""

import json
from pathlib import Path
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server Settings
    PROJECT_NAME: str = "RoadGuard AI"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database Settings
    DATABASE_URL: str = "sqlite:///./roadguard.db"

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ]

    # File Storage Settings
    EVIDENCE_STORAGE_DIR: str = "./storage/evidence"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
    ]

    # Model & Inference Settings
    MODEL_NAME: str = "YOLO11s"
    MODEL_CHECKPOINT_PATH: str = "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt"
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.25
    DEFAULT_IOU_THRESHOLD: float = 0.7
    DEFAULT_IMAGE_SIZE: int = 720

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    return json.loads(v_trimmed)
                except Exception:
                    pass
            return [i.strip() for i in v_trimmed.split(",") if i.strip()]
        return v

    @property
    def evidence_storage_path(self) -> Path:
        """Resolved Path object for evidence storage directory."""
        path = Path(self.EVIDENCE_STORAGE_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
