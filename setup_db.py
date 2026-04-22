import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.connection import init_db

if __name__ == "__main__":
    print("=" * 50)
    print("Marico Reconciliation - Database Setup")
    print("=" * 50)
    init_db()