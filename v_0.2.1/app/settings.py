# database/settings.py
# manual of setting management
# https://docs.pydantic.dev/2.11/concepts/pydantic_settings/

# from typing import Any

# from pydantic import (
#     BaseModel,
#     Field,
#     AliasChoices,
#     ImportString,
#     PostgresDsn,
# )
# from pydantic import ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_name: str
    database_url: str
    endpoint: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# 設定インスタンスを生成（どこでもインポートして利用できます）
settings = Settings()

print(Settings().model_dump()) # 本番環境ではコメントアウトする

