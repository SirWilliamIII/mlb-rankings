from app.services.database_manager import DatabaseManager
import os
print("Initializing DatabaseManager...")
print(f"DATABASE_URL env var: {os.getenv('DATABASE_URL')}")
db = DatabaseManager()
print("DatabaseManager initialized.")