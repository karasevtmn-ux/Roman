import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JW_", extra="ignore")

    app_name: str = "Justice Watcher"
    data_dir: Path = Field(default=Path.home() / "JusticeWatcher")
    db_file: str = "justice_watcher.db"
    local_config_file: str = "local_settings.json"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_login: str = "justicewatcher604@gmail.com"
    smtp_sender: str = "justicewatcher604@gmail.com"
    smtp_password: str = ""

    check_window_start: str = "01:00"
    check_window_end: str = "05:00"
    retry_interval_minutes: int = 30

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_file

    @property
    def local_config_path(self) -> Path:
        return self.data_dir / self.local_config_file


def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    if settings.local_config_path.exists():
        try:
            data = json.loads(settings.local_config_path.read_text(encoding="utf-8"))
            settings = settings.model_copy(update=data)
        except json.JSONDecodeError:
            pass

    return settings


def save_settings(settings: AppSettings) -> None:
    payload = {
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_login": settings.smtp_login,
        "smtp_sender": settings.smtp_sender,
        "smtp_password": settings.smtp_password,
        "check_window_start": settings.check_window_start,
        "check_window_end": settings.check_window_end,
        "retry_interval_minutes": settings.retry_interval_minutes,
    }
    settings.local_config_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
