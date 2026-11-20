import sys
from app.core.database import engine
from sqlalchemy import text
from app.models.project import Playlist
from app.core.database import Base

Base.metadata.create_all(bind=engine)

with engine.connect() as conn:
    for col, col_def in [
        ("resumable_upload_url", "VARCHAR"),
        ("bytes_uploaded", "INTEGER DEFAULT 0"),
        ("total_bytes", "INTEGER DEFAULT 0"),
        ("retry_count", "INTEGER DEFAULT 0"),
        ("playlist_id", "VARCHAR"),
        ("thumbnail_attached", "BOOLEAN DEFAULT 0"),
    ]:
        try:
            conn.execute(text(f"ALTER TABLE publish_jobs ADD COLUMN {col} {col_def};"))
            conn.commit()
            print(f"Added column {col}")
        except Exception as e:
            print(f"Column {col} already exists or skipped: {e}")

print("Migration completed.")
