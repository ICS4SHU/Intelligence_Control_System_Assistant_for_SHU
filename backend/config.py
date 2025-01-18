from starlette.config import Config

config = Config(".env")

API_KEY = config("API_KEY")
API_BASE_URL = config("API_BASE_URL")
CHAT_ID = config("CHAT_ID")

FRONTEND_ORIGIN = config("FRONTEND_ORIGIN")

VITE_API_BASE_URL = config("VITE_API_BASE_URL")
