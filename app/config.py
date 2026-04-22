import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

class Config:
    ENV = os.getenv('ENV', 'development')
    
    @classmethod
    def get_database_url(cls):
        if cls.ENV == 'production':
            return os.getenv('DATABASE_URL')
        else:
            sqlite_path = os.getenv('SQLITE_PATH', 'database/dev.db')
            full_path = BASE_DIR / sqlite_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            return f'sqlite:///{full_path}'
    
    @classmethod
    def get_engine_args(cls):
        if cls.ENV == 'production':
            return {}
        return {'connect_args': {'check_same_thread': False}}