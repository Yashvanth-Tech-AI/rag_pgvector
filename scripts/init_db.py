import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.database import Database


if __name__ == "__main__":
    settings = get_settings()
    Database(settings.database_url).initialize()
    print("Database initialized successfully.")

