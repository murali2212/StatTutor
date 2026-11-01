import contextvars
import os
import re
import sqlite3
import threading
from uuid import UUID

DB_PATH = os.environ.get(
    "STATTUTOR_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "stattutor.db"),
)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL", "")
APP_ENCRYPTION_KEY = os.environ.get("APP_ENCRYPTION_KEY", "")
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_ANON_KEY and SUPABASE_DB_URL)
CONFIGURED_VALUES = (SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_DB_URL)

if any(CONFIGURED_VALUES) and not SUPABASE_ENABLED:
    raise RuntimeError(
        "Supabase requires SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_DB_URL."
    )
if SUPABASE_ENABLED and not APP_ENCRYPTION_KEY:
    raise RuntimeError("Supabase deployments also require APP_ENCRYPTION_KEY.")
if os.environ.get("VERCEL") == "1" and not SUPABASE_ENABLED:
    raise RuntimeError(
        "Vercel requires Supabase. Configure SUPABASE_URL, SUPABASE_ANON_KEY, "
        "SUPABASE_DB_URL, and APP_ENCRYPTION_KEY."
    )

_user_id = contextvars.ContextVar("stattutor_user_id", default=None)
_initialized_users = set()
_initialization_lock = threading.Lock()


def set_user_id(user_id):
    return _user_id.set(user_id)


def reset_user_id(token):
    _user_id.reset(token)


def schema_for_user(user_id):
    try:
        normalized = UUID(str(user_id)).hex
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Supabase returned an invalid user ID.") from exc
    return "stattutor_" + normalized


class _PostgresRow(dict):
    def __init__(self, names, values):
        super().__init__(zip(names, values))
        self._values = values

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)


def _row_factory(cursor):
    names = [column.name for column in cursor.description]
    return lambda values: _PostgresRow(names, values)


class _PostgresConnection:
    def __init__(self, connection):
        self._connection = connection

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._connection.__exit__(exc_type, exc_value, traceback)

    def execute(self, query, params=()):
        return self._connection.execute(re.sub(r"\?", "%s", query), params)


def conn():
    if not SUPABASE_ENABLED:
        os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
        c = sqlite3.connect(DB_PATH)
        c.execute("PRAGMA foreign_keys=ON")
        c.row_factory = sqlite3.Row
        return c

    user_id = _user_id.get()
    if user_id is None:
        raise RuntimeError("A verified user is required to access Supabase data.")
    import psycopg

    schema = schema_for_user(user_id)
    connection = psycopg.connect(SUPABASE_DB_URL, row_factory=_row_factory)
    connection.execute(f'SET search_path TO "{schema}"')
    return _PostgresConnection(connection)


_POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_keys (
    id BIGSERIAL PRIMARY KEY, provider TEXT NOT NULL, model TEXT NOT NULL,
    api_key TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY, role TEXT NOT NULL, content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, sources TEXT
);
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY, kind TEXT NOT NULL, filename TEXT NOT NULL,
    text TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS units (
    id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS topics (
    id BIGSERIAL PRIMARY KEY,
    unit_id BIGINT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    name TEXT NOT NULL, position INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started'
);
CREATE TABLE IF NOT EXISTS questions (
    id BIGSERIAL PRIMARY KEY, paper TEXT NOT NULL, number TEXT, text TEXT NOT NULL,
    marks DOUBLE PRECISION, qtype TEXT NOT NULL DEFAULT 'mixed',
    topic_id BIGINT REFERENCES topics(id) ON DELETE SET NULL,
    alt INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS paper_meta (
    paper TEXT PRIMARY KEY, max_marks DOUBLE PRECISION, note TEXT
);
CREATE TABLE IF NOT EXISTS materials (
    id BIGSERIAL PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'notes',
    chars INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    material_id BIGINT NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    position INTEGER NOT NULL, text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_mat ON chunks(material_id);
CREATE INDEX IF NOT EXISTS idx_q_paper ON questions(paper);
CREATE INDEX IF NOT EXISTS idx_t_unit ON topics(unit_id);
CREATE TABLE IF NOT EXISTS learner (
    key TEXT PRIMARY KEY, val INTEGER NOT NULL DEFAULT 0
);
"""


def init():
    if SUPABASE_ENABLED:
        with conn() as c:
            for statement in _POSTGRES_SCHEMA.split(";"):
                if statement.strip():
                    c.execute(statement)
        return

    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS api_keys(
            id INTEGER PRIMARY KEY,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            api_key TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY, kind TEXT NOT NULL, filename TEXT NOT NULL,
            text TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS units(
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, position INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS topics(
            id INTEGER PRIMARY KEY, unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
            name TEXT NOT NULL, position INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'not_started');
        CREATE TABLE IF NOT EXISTS questions(
            id INTEGER PRIMARY KEY, paper TEXT NOT NULL, number TEXT, text TEXT NOT NULL,
            marks REAL, qtype TEXT NOT NULL DEFAULT 'mixed',
            topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
            alt INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS paper_meta(paper TEXT PRIMARY KEY, max_marks REAL, note TEXT);
        CREATE TABLE IF NOT EXISTS materials(
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'notes',
            chars INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS chunks(
            id INTEGER PRIMARY KEY, material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
            position INTEGER NOT NULL, text TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_chunks_mat ON chunks(material_id);
        CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(text, chunk_id UNINDEXED, material_id UNINDEXED, tokenize='porter unicode61');
        CREATE TABLE IF NOT EXISTS learner(key TEXT PRIMARY KEY, val INTEGER NOT NULL DEFAULT 0);
        CREATE INDEX IF NOT EXISTS idx_q_paper ON questions(paper);
        CREATE INDEX IF NOT EXISTS idx_t_unit ON topics(unit_id);
        """)

    with conn() as c:
        cols = [r[1] for r in c.execute("PRAGMA table_info(questions)")]
        mcols = [r[1] for r in c.execute("PRAGMA table_info(messages)")]
        if "sources" not in mcols:
            c.execute("ALTER TABLE messages ADD COLUMN sources TEXT")
        if "alt" not in cols:
            c.execute("ALTER TABLE questions ADD COLUMN alt INTEGER NOT NULL DEFAULT 0")


def initialize_user(user_id):
    if not SUPABASE_ENABLED:
        return
    schema = schema_for_user(user_id)
    if schema in _initialized_users:
        return

    with _initialization_lock:
        if schema in _initialized_users:
            return
        import psycopg

        with psycopg.connect(SUPABASE_DB_URL) as connection:
            connection.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        with psycopg.connect(SUPABASE_DB_URL) as lock_connection:
            lock_connection.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (schema,)
            )
            token = set_user_id(user_id)
            try:
                init()
                from . import seed

                seed.seed_if_empty()
                seed.seed_materials()
            finally:
                reset_user_id(token)
        _initialized_users.add(schema)
