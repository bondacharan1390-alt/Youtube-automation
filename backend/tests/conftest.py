import pytest
from app.core.database import engine, Base, SessionLocal
from app.main import seed_initial_data

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_data(db)
        # Test sessions represent a new local calendar day.
        from app.models.user import Channel
        for channel in db.query(Channel).all():
            channel.quota_units_used_today = 150
        from app.models.project import PublishJob
        db.query(PublishJob).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    yield
