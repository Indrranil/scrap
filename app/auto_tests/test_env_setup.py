"""
Test environment setup - must be imported first before any other app modules
"""
import os
import sys
from pathlib import Path

# Set testing environment variables BEFORE any other imports
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("🔧 Test environment configured - using SQLite database")
