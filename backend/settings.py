from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    CBF_MODEL_PATH: str = "./cbf/outputs/models/best_cbf_model_tfidf.pkl"
    CF_MODEL_PATH: str = "./cf/outputs/models/best_cf_model_ncf.pkl"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  

