from pathlib import Path
import os

from dotenv import load_dotenv


# Load environment variables from a local .env file located in the project root
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)


# API keys and paths
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")

# Path to your Google OAuth client secrets JSON file
# Defaults to "client_secret.json" in the project if not provided
CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "client_secret.json")

