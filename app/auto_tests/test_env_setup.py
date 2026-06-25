"""
Test environment setup - must be imported first before any other app modules
"""
import os
import sys
from pathlib import Path

os.environ["TESTING"] = "1"
os.environ["JWT_SECRET"] = "test-secret-key"

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
