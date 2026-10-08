import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
import app.database as app_database
import app.services.background_worker as bg_worker
from app.main import app

@pytest.fixture(scope="session")
def temp_storage():
    """Create a temporary directory for test generated certificates and archives."""
    temp_dir = Path(tempfile.mkdtemp(prefix="bulk_cert_test_"))
    certs_dir = temp_dir / "certificates"
    archives_dir = temp_dir / "archives"
    certs_dir.mkdir(parents=True, exist_ok=True)
    archives_dir.mkdir(parents=True, exist_ok=True)

    # Patch settings paths
    orig_storage = settings.STORAGE_DIR
    orig_certs = settings.CERTIFICATES_DIR
    orig_archives = settings.ARCHIVES_DIR

    settings.STORAGE_DIR = temp_dir
    settings.CERTIFICATES_DIR = certs_dir
    settings.ARCHIVES_DIR = archives_dir

    yield temp_dir

    # Teardown
    settings.STORAGE_DIR = orig_storage
    settings.CERTIFICATES_DIR = orig_certs
    settings.ARCHIVES_DIR = orig_archives
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def setup_test_db(temp_storage):
    """Set up a fresh SQLite database file for each test."""
    test_db_path = temp_storage / f"test_{tempfile.mktemp().split(os.sep)[-1]}.db"
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Patch database engine and SessionLocal in app.database and background_worker
    orig_engine = app_database.engine
    orig_session_local = app_database.SessionLocal
    orig_bg_session_local = bg_worker.SessionLocal

    app_database.engine = test_engine
    app_database.SessionLocal = TestSessionLocal
    bg_worker.SessionLocal = TestSessionLocal

    yield TestSessionLocal

    # Teardown
    app_database.engine = orig_engine
    app_database.SessionLocal = orig_session_local
    bg_worker.SessionLocal = orig_bg_session_local

    Base.metadata.drop_all(bind=test_engine)
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass

@pytest.fixture(scope="function")
def db_session(setup_test_db):
    session = setup_test_db()
    yield session
    session.close()

@pytest.fixture(scope="function")
def client(setup_test_db):
    def override_get_db():
        db = setup_test_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
