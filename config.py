import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    """Base configuration with shared settings."""
    AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    PRIORITY_QUEUE = os.getenv("P1_QUEUE_URL", "https://prod-queue-url")
    TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "https://prod-teams-url")


class TestConfig(BaseConfig):
    """Test configuration with mock settings"""
    def __init__(self,queue_url):
        self.PRIORITY_QUEUE = queue_url
