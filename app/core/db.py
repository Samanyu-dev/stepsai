"""
Steps AI Database Persistence Infrastructure.

This module initializes the database tables and provides multi-driver support
for both SQLite (local development) and PostgreSQL (production deployment).
It manages connection mapping and automatically translates SQL syntax placeholders transparently.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class PostgresCursorWrapper:
    """
    Wrapper cursor around psycopg2 RealDictCursor that maps SQLite-style
    queries (like '?' placeholders) into PostgreSQL '%s' style seamlessly.
    """
    def __init__(self, pg_cursor):
        self.cursor = pg_cursor

    def execute(self, sql: str, parameters: tuple = ()):
        # Dynamically translate '?' placeholders to psycopg2 '%s'
        sql_pg = sql.replace('?', '%s')
        self.cursor.execute(sql_pg, parameters)
        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def rowcount(self):
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()

    def __iter__(self):
        return iter(self.cursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class PostgresConnectionWrapper:
    """
    Wrapper connection around psycopg2 connection mapping SQLite-style
    shorthands (like conn.execute()) to Postgres-compatible methods.
    """
    def __init__(self, pg_conn):
        self.conn = pg_conn

    def cursor(self):
        return PostgresCursorWrapper(self.conn.cursor())

    def execute(self, sql: str, parameters: tuple = ()):
        cursor = self.cursor()
        cursor.execute(sql, parameters)
        return cursor

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

def is_postgres() -> bool:
    """
    Helper to detect if the database configuration specifies PostgreSQL.
    """
    from app.core.config import settings
    url = settings.DATABASE_URL
    return url.startswith("postgresql://") or url.startswith("postgres://") or url.startswith("postgresql+psycopg2://")

def init_db():
    """
    Initializes the database schema if tables do not exist.
    Supports both SQLite and PostgreSQL SQL syntax and types.
    """
    from app.core.config import settings
    url = settings.DATABASE_URL
    
    if is_postgres():
        import psycopg2
        logger.info("Initializing PostgreSQL schema...")
        conn = psycopg2.connect(url)
        try:
            cursor = conn.cursor()
            
            # Resumes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                session_id TEXT PRIMARY KEY,
                profile_json TEXT,
                resume_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Interviews table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                interview_session_id TEXT PRIMARY KEY,
                resume_session_id TEXT,
                interview_mode TEXT,
                difficulty_level TEXT,
                current_question_index INTEGER DEFAULT 1,
                total_questions INTEGER,
                messages_json TEXT,
                completed INTEGER DEFAULT 0,
                resume_context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Evaluations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                session_id TEXT PRIMARY KEY,
                overall_score INTEGER,
                report_json TEXT,
                pdf_bytes BYTEA,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Messages table (PostgreSQL SERIAL identity)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                session_id TEXT,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Migration: alter table created_at if missing
            try:
                cursor.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            except Exception:
                pass
                
            conn.commit()
            logger.info("PostgreSQL database schema successfully initialized!")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL database: {str(e)}", exc_info=True)
            raise e
        finally:
            conn.close()
    else:
        import sqlite3
        logger.info("Initializing SQLite schema...")
        conn = sqlite3.connect(url)
        try:
            cursor = conn.cursor()
            
            # Resumes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                session_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            try:
                cursor.execute("ALTER TABLE resumes ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            except Exception:
                pass
            
            # Interviews table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                interview_session_id TEXT PRIMARY KEY,
                resume_session_id TEXT NOT NULL,
                interview_mode TEXT NOT NULL,
                difficulty_level TEXT NOT NULL,
                current_question_index INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                messages_json TEXT NOT NULL,
                completed INTEGER NOT NULL,
                resume_context TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Evaluations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                session_id TEXT PRIMARY KEY,
                overall_score INTEGER NOT NULL,
                report_json TEXT NOT NULL,
                pdf_bytes BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Messages table (SQLite AUTOINCREMENT identity)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            conn.commit()
            logger.info("SQLite database schema successfully initialized and verified!")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {str(e)}", exc_info=True)
            raise e
        finally:
            conn.close()

def get_db_connection():
    """
    Returns a thread-safe connection to either PostgreSQL or SQLite depending on environment settings.
    Uses dictionary-like mapping for columns access.
    """
    from app.core.config import settings
    url = settings.DATABASE_URL
    
    if is_postgres():
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
        return PostgresConnectionWrapper(conn)
    else:
        import sqlite3
        conn = sqlite3.connect(url)
        conn.row_factory = sqlite3.Row
        return conn
