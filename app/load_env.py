# This file loads environment variables from the .env file in the project root
from pathlib import Path
from dotenv import load_dotenv
import os

# Find the .env file in the parent directory (project root)
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
