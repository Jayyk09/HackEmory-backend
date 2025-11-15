import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment/.env")


def get_db_conn():
    """Get a new database connection using DATABASE_URL."""
    return psycopg2.connect(DATABASE_URL)
