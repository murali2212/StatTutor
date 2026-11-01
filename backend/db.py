import os, sqlite3

DB_PATH = os.environ.get(
    "STATTUTOR_DB",
    os.path.join(os.path.dirname(__file__), "..", "data", "stattutor.db"),
)

def conn():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute("PRAGMA foreign_keys=ON")
    c.row_factory = sqlite3.Row
    return c

def init():
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

    with conn() as c:   # upgrade databases made by an earlier version
        cols = [r[1] for r in c.execute("PRAGMA table_info(questions)")]
        mcols = [r[1] for r in c.execute("PRAGMA table_info(messages)")]
        if "sources" not in mcols:
            c.execute("ALTER TABLE messages ADD COLUMN sources TEXT")
        if "alt" not in cols:
            c.execute("ALTER TABLE questions ADD COLUMN alt INTEGER NOT NULL DEFAULT 0")
