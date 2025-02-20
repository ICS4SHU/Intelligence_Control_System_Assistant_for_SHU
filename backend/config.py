from starlette.config import Config
from enum import Enum


config = Config(".env")

class AgentID(Enum):
    REVISION = "e3cfde42ed1a11ef9f240242ac120006"
    DRIVEEXAMIN = "d8214c5ee7aa11efa80f0242ac120003"
    HOMEWORK = "e7074ec2eace11ef8da20242ac120003"
    
CHAT_ID = config("CHAT_ID")


API_KEY = config("API_KEY")
API_BASE_URL = config("API_BASE_URL")


FRONTEND_ORIGIN = config("FRONTEND_ORIGIN")

VITE_API_BASE_URL = config("VITE_API_BASE_URL")

