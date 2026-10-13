from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The .env lives at the repo root; also honour a backend/.env override and the CWD one.
_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_REPO_ROOT / ".env"), str(_REPO_ROOT / "backend" / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "InfraManager"
    database_url: str = "postgresql+psycopg://inframanager:inframanager@localhost:5432/inframanager"

    secret_key: str = "change-me"
    encryption_key: str = ""
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    admin_username: str = "admin"
    admin_password: str = "admin"

    proxmox_url: str = ""
    proxmox_token_id: str = ""
    proxmox_token_secret: str = ""
    proxmox_tls_verify: bool = True
    proxmox_sync_seconds: int = 30

    veeam_api_url: str = ""
    veeam_username: str = ""
    veeam_password: str = ""
    veeam_sync_seconds: int = 300

    storage_warning_threshold: int = 80
    storage_critical_threshold: int = 90
    storage_full_threshold: int = 95

    scheduler_enabled: bool = True
    auto_create_tables: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
