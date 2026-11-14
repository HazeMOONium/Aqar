"""Database connection helper for the Aqar client application.

Configuration resolution order:
  1. `st.secrets` (Streamlit Community Cloud - set in the app's Secrets UI)
  2. `.env` file (local development)
"""
import os

from dotenv import load_dotenv

# Load .env for local runs (harmless if absent)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def get_db_config():
    cfg = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "user": os.getenv("DB_USERNAME"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_DATABASE"),
    }
    # On Streamlit Community Cloud there is no .env -> read from st.secrets
    try:
        import streamlit as st
        for key in list(cfg.keys()):
            if cfg[key] in (None, "") and key in st.secrets:
                cfg[key] = st.secrets[key]
    except Exception:
        pass  # not running inside Streamlit (e.g. setup scripts)
    return cfg


def get_connection():
    """Return a new connection to the REMOTE MySQL server (never localhost)."""
    import mysql.connector

    cfg = get_db_config()
    return mysql.connector.connect(
        host=cfg["host"],
        port=int(cfg["port"] or 3306),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        connection_timeout=20,
        autocommit=False,
    )
