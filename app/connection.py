from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import Config
from app.models import Base

_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        database_url = Config.get_database_url()
        engine_args = Config.get_engine_args()
        _engine = create_engine(database_url, **engine_args)
    return _engine

def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(bind=engine)
    return _SessionLocal()

def init_db():
    """Create all tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print(f"✅ Database initialized")
    print(f"   Environment: {Config.ENV}")
    print(f"   URL: {engine.url}")
    return engine

def drop_db():
    """Drop all tables (careful!)"""
    confirm = input("Drop all tables? Type 'yes' to confirm: ")
    if confirm == 'yes':
        engine = get_engine()
        Base.metadata.drop_all(engine)
        print("✅ All tables dropped")
    else:
        print("Cancelled")