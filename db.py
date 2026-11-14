"""Database connection helper for the Aqar client application."""
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USERNAME", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_DATABASE", "aqar"),
    }


def get_connection():
    """Return a new connection to the REMOTE MySQL server (never localhost)."""
    return mysql.connector.connect(
        host=get_db_config()["host"],
        port=get_db_config()["port"],
        user=get_db_config()["user"],
        password=get_db_config()["password"],
        database=get_db_config()["database"],
        connection_timeout=20,
        autocommit=False,
    )
