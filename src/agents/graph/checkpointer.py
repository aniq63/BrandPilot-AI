import atexit
import os
from pathlib import Path

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")

with PostgresSaver.from_conn_string(DATABASE_URL) as setup_saver:
    setup_saver.setup()

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    open=True,
)

atexit.register(pool.close)

checkpointer = PostgresSaver(pool)
