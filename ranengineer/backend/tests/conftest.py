import pytest
from app.config.database import SessionLocal, Base, engine

@pytest.fixture(autouse=True)
def clear_db():
    """Clear all data from tables before each test."""
    with SessionLocal() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()

