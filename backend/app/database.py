from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_fts5(engine_=None):
    """Create FTS5 virtual tables and triggers if they don't exist.

    Uses the SQLAlchemy engine's connect() to ensure proper connection sharing.

    Args:
        engine_: Optional SQLAlchemy engine. Defaults to the module-level engine.
    """
    eng = engine_ or engine
    with eng.connect() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS contracts_fts USING fts5(
                title,
                content,
                content='contracts',
                content_rowid='id'
            )
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS contracts_ai AFTER INSERT ON contracts BEGIN
                INSERT INTO contracts_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
            END
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS contracts_ad AFTER DELETE ON contracts BEGIN
                INSERT INTO contracts_fts(contracts_fts, rowid, title, content) VALUES('delete', old.id, old.title, old.content);
            END
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS contracts_au AFTER UPDATE ON contracts BEGIN
                INSERT INTO contracts_fts(contracts_fts, rowid, title, content) VALUES('delete', old.id, old.title, old.content);
                INSERT INTO contracts_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
            END
        """))
        conn.commit()
