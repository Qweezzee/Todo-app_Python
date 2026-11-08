"""Check migration SQL and preservation of tables created before Alembic."""

import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class MigrationTests(unittest.TestCase):
    def test_sql_and_existing_categories(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "test.db"
            env = dict(os.environ, DATABASE_URL=f"sqlite:///{db_path}")
            command = [sys.executable, "-m", "alembic", "upgrade", "head"]
            cwd = Path(__file__).resolve().parents[1]
            result = subprocess.run(
                command + ["--sql"],
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("CREATE TABLE IF NOT EXISTS categories", result.stdout)
            self.assertIn("CREATE TABLE tasks", result.stdout)
            with sqlite3.connect(db_path) as connection:
                connection.execute(
                    "CREATE TABLE categories (name VARCHAR NOT NULL, "
                    "id VARCHAR PRIMARY KEY NOT NULL)"
                )
                connection.execute(
                    "INSERT INTO categories VALUES ('Existing category', 'existing-id')"
                )
            subprocess.run(command, cwd=cwd, env=env, capture_output=True, check=True)
            with sqlite3.connect(db_path) as connection:
                self.assertEqual(
                    connection.execute("SELECT name, id FROM categories").fetchall(),
                    [("Existing category", "existing-id")],
                )
                self.assertEqual(
                    connection.execute("SELECT * FROM tasks").fetchall(), []
                )
