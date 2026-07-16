import pytest
import os
import sys

# Ensure backend folder is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db
from app.models.crm import HCP

# Setup test DB (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Seed initial test data
    db = TestingSessionLocal()
    try:
        # Seed test HCPs
        hcp1 = HCP(full_name="Dr. Priya Sharma", specialty="Cardiology", organization="Metro Heart Institute", email="priya.sharma@metroheart.com")
        hcp2 = HCP(full_name="Dr. Alan Grant", specialty="Oncology", organization="City Cancer Research Center", email="alan.grant@citycancer.org")
        db.add(hcp1)
        db.add(hcp2)
        db.commit()
        yield db
    finally:
        db.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
