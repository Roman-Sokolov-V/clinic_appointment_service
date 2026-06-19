import os
import dotenv

dotenv.load_dotenv()

IN_DOCKER = os.getenv("IN_DOCKER", "false").lower() == "true"

if IN_DOCKER:
    basic_url = "http://clinic:8000/"
else:
    basic_url = "http://127.0.0.1:8000/"

REG_URL= basic_url + "users/"
TOKEN_URL = basic_url + "users/token/"

POSTGRES_USER=os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DB=os.getenv("POSTGRES_DB", "postgres")
# Хост — це назва сервісу бази даних у docker-compose
POSTGRES_HOST=os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT=os.getenv("POSTGRES_PORT", "5432")

REDIS_URL=os.getenv("REDIS_URL", "redis://redis:6379")

TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN")
TOKEN_LIFETIME = 900 # 15 minutes
