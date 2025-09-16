#!/usr/bin/env python3
"""
Startup script for the carpool API that handles database migration and server startup
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command with error handling"""
    print(f" {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f" {description} successful")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f" {description} failed")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f" {description} timed out")
        return False
    except Exception as e:
        print(f" {description} error: {e}")
        return False

def main():
    print("🚀 Starting Carpool API...")
    
    # Set working directory - use current directory for local, /app for Docker
    if os.path.exists('/app'):
        os.chdir('/app')
    else:
        # For local development, stay in current directory
        print("Running in local development mode")
    
    # Check if we're in production (Cloud Run)
    is_production = os.getenv('K_SERVICE') is not None
    database_url = os.getenv('DATABASE_URL')
    
    print(f"Environment: {'Production (Cloud Run)' if is_production else 'Development'}")
    print(f"Database URL: {database_url[:50] + '...' if database_url else 'Not set'}")
    
    # Run database migration if we have a database URL
    if database_url and database_url.startswith('postgresql'):
        print("🗄️ Running database migration...")
        if not run_command("alembic upgrade head", "Database migration"):
            print("⚠️ Migration failed, but continuing with startup...")
    else:
        print("ℹ️ No PostgreSQL database configured, skipping migration")
    
    # Start the server
    port = os.getenv('PORT', '8000')
    host = '0.0.0.0'
    
    print(f"🌐 Starting server on {host}:{port}")
    
    # Use exec to replace the process (important for Cloud Run)
    cmd = f"uvicorn src.carpool.api:app --host {host} --port {port} --timeout-keep-alive 300"
    print(f"Command: {cmd}")
    
    os.execvp('uvicorn', [
        'uvicorn',
        'src.carpool.api:app',
        '--host', host,
        '--port', port,
        '--timeout-keep-alive', '300',
        '--access-log'
    ])

if __name__ == "__main__":
    main()
