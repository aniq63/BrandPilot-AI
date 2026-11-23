import os
import sys
import unittest
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

try:
    from database import connection as db_connection
    IMPORT_ERROR = None
except Exception as exc:
    db_connection = None
    IMPORT_ERROR = exc


class DatabaseConnectionTests(unittest.TestCase):
    def require_connection_module(self):
        if IMPORT_ERROR is not None:
            self.fail(
                "Cannot load database.connection: "
                f"{type(IMPORT_ERROR).__name__}: {IMPORT_ERROR}. "
                "Check DATABASE_URL in .env and install a PostgreSQL DBAPI "
                "driver such as psycopg[binary]."
            )
        return db_connection

    def assert_select_one(self, execute, module):
        url = module.engine.url.render_as_string(hide_password=True)
        try:
            result = execute(text("SELECT 1")).scalar_one()
        except Exception as exc:
            self.fail(
                f"Database query failed ({url}): "
                f"{type(exc).__name__}: {exc}"
            )
        self.assertEqual(result, 1)

    def test_database_url_is_configured(self):
        url = os.getenv("DATABASE_URL")
        self.assertTrue(url, "DATABASE_URL is missing from .env")
        self.assertTrue(url.strip(), "DATABASE_URL is empty in .env")
        self.assertNotIn("your-", url)
        self.assertNotIn("<", url)

    def test_engine_is_created(self):
        module = self.require_connection_module()
        self.assertIsNotNone(module.engine)
        self.assertEqual(module.engine.url.get_backend_name(), "postgresql")
        self.assertIsNotNone(module.engine.pool)

    def test_engine_connects(self):
        module = self.require_connection_module()
        with module.engine.connect() as connection:
            self.assert_select_one(connection.execute, module)

    def test_session_factory_connects(self):
        module = self.require_connection_module()
        with module.SessionLocal() as session:
            self.assert_select_one(session.execute, module)

    def test_get_db_yields_working_session_and_closes_it(self):
        module = self.require_connection_module()
        generator = module.get_db()
        session = next(generator)
        try:
            self.assert_select_one(session.execute, module)
        finally:
            with self.assertRaises(StopIteration):
                next(generator)


if __name__ == "__main__":
    unittest.main(verbosity=2)
