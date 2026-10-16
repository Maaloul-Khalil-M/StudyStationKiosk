"""SQLite database connection and schema initialization."""

from pathlib import Path
import os
import sqlite3
import sys


def get_default_db_path() -> Path:
    """Return platform-standard path for Study Station database (active user)."""
    try:
        from study_station.persistence.user_manager import UserManager
        return UserManager().get_user_db_path()
    except Exception:
        if sys.platform == "win32":
            app_data = os.environ.get("APPDATA")
            base_dir = Path(app_data) if app_data else Path.home() / "AppData" / "Roaming"
        else:
            xdg_data = os.environ.get("XDG_DATA_HOME")
            base_dir = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"

        db_dir = base_dir / "study_station"
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / "studystation.db"


class Database:
    """Manages SQLite connection lifecycle and schema setup."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path == ":memory:":
            self.db_path = ":memory:"
        elif db_path is not None:
            self.db_path = str(Path(db_path).resolve())
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = str(get_default_db_path())

        self._conn: sqlite3.Connection | None = None
        self._init_connection()
        self._create_schema()

    def _init_connection(self) -> None:
        self._conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        # WAL mode for crash-safety and fast concurrent reads on spinning disks
        if self.db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode = WAL;")
        self._conn.execute("PRAGMA synchronous = NORMAL;")
        self._conn.execute("PRAGMA foreign_keys = ON;")

    def _create_schema(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self._conn:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS study_logs (
                    id TEXT PRIMARY KEY,
                    subject_name TEXT NOT NULL,
                    study_cycle_id TEXT,
                    started_at TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    source TEXT NOT NULL DEFAULT 'timer'
                );

                CREATE INDEX IF NOT EXISTS idx_study_logs_subject_started
                ON study_logs(subject_name, started_at);

                CREATE TABLE IF NOT EXISTS subject_targets (
                    subject_name TEXT PRIMARY KEY,
                    target_minutes INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS timetable_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    subject_name TEXT NOT NULL,
                    core TEXT NOT NULL DEFAULT 'COURS',
                    location TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS active_timer_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    is_active INTEGER NOT NULL,
                    subject_name TEXT NOT NULL,
                    total_duration_minutes INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    target_end_time TEXT NOT NULL,
                    is_paused INTEGER NOT NULL DEFAULT 0,
                    paused_remaining_seconds INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS study_todos (
                    id TEXT PRIMARY KEY,
                    subject_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    completed_at TEXT,
                    confidence TEXT,
                    next_class_question TEXT,
                    session_ref_id TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_study_todos_subject ON study_todos(subject_name);
                CREATE INDEX IF NOT EXISTS idx_study_todos_status ON study_todos(status);
                CREATE INDEX IF NOT EXISTS idx_study_todos_due ON study_todos(due_date);

                CREATE TABLE IF NOT EXISTS special_periods (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    period_type TEXT NOT NULL DEFAULT 'exam',
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    overrides_schedule INTEGER NOT NULL DEFAULT 1,
                    notes TEXT DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_special_periods_dates ON special_periods(start_date, end_date);
            """)

            # Run migration for existing databases: check if todo_id exists in study_logs
            cursor = self._conn.execute("PRAGMA table_info(study_logs);")
            columns = [row["name"] for row in cursor.fetchall()]
            if "todo_id" not in columns:
                self._conn.execute("ALTER TABLE study_logs ADD COLUMN todo_id TEXT;")

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._init_connection()
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
