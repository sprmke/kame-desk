from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://doctordesk:doctordesk_local_only@127.0.0.1:5432/doctordesk"
    )
    redis_url: str = "redis://127.0.0.1:6379/0"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    patient_access_token_expire_minutes: int = 30
    financing_partner_enabled: bool = False
    cors_origins: str = "http://localhost:3100"
    environment: str = "local"
    algorithm: str = "HS256"
    web_base_url: str = "http://localhost:3100"

    # R2 / MinIO (local dev uses MinIO from docker-compose)
    s3_endpoint_url: str = "http://127.0.0.1:9000"
    s3_access_key: str = "doctordesk"
    s3_secret_key: str = "doctordesk_local_only"
    s3_bucket: str = "doctordesk"
    s3_region: str = "us-east-1"

    # Email (Mailhog locally)
    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    smtp_from: str = "noreply@doctordesk.local"

    platform_ai_assistant_enabled: bool = False
    platform_admin_emails: str = ""

    # WhatsApp Business Cloud API (Phase 35) — one Meta App/webhook per
    # deployment; individual clinics' phone_number_id + access_token are
    # stored per-clinic (see Clinic.whatsapp_*).
    whatsapp_webhook_verify_token: str = "dev-whatsapp-verify-token"

    # AI (Phase 14+)
    openai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_daily_request_cap: int = 100

    # Embeddings / transcription (Phase 15+)
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 256
    embedding_model_version: str = "stub-v1"
    recording_retention_days: int = 90
    transcription_timeout_minutes: int = 30

    # Web Push (Phase 40 in-app notifications)
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:noreply@doctordesk.local"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def platform_admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.platform_admin_emails.split(",") if e.strip()]


settings = Settings()
