#!/usr/bin/env python3
"""
Script to run the TinyDB to PostgreSQL migration
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def main():
    print("🚀 Starting carpool app migration...")
    
    try:
        # Import database functions
        from src.carpool.database import health_check, create_tables, get_database_info
        
        # Show database configuration
        db_info = get_database_info()
        print(f"📋 Database: {db_info['type']} ({db_info['environment']})")
        print(f"📋 URL: {db_info['url']}")
        
        # Test database connection
        print("📋 Testing database connection...")
        if not health_check():
            print("❌ Database connection failed.")
            return False
        
        print("✅ Database connection successful!")
        
        # Create tables
        print("📋 Creating database tables...")
        create_tables()
        print("✅ Database tables created!")
        
        # Run migration if TinyDB data exists
        tinydb_path = project_root / "data" / "db.json"
        if tinydb_path.exists():
            print("📋 Found TinyDB data, running migration...")
            from migrate_tinydb_to_postgres import main as migrate_main
            migrate_main()
        else:
            print("📋 No TinyDB data found, skipping migration.")
        
        print("🎉 Setup completed successfully!")
        print(f"💡 Database type: {db_info['type']}")
        if db_info['type'] == 'SQLite':
            print("💡 For production, set DATABASE_URL environment variable to use PostgreSQL")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
