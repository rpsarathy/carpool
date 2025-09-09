#!/usr/bin/env python3
"""
Migration script to transfer data from TinyDB to PostgreSQL
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from tinydb import TinyDB
from sqlalchemy.orm import sessionmaker
from src.carpool.database import engine, User, Group, OnDemandRequest, create_tables

def backup_tinydb():
    """Create a backup of the TinyDB file before migration"""
    repo_root = Path(__file__).resolve().parent
    db_path = repo_root / "data" / "db.json"
    
    if db_path.exists():
        backup_path = repo_root / "data" / f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(db_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return db_path
    else:
        print("⚠️  No TinyDB file found to migrate")
        return None

def migrate_users(tinydb_path, session):
    """Migrate users from TinyDB to PostgreSQL"""
    db = TinyDB(tinydb_path)
    users_table = db.table("users")
    
    migrated_count = 0
    for user_data in users_table.all():
        # Check if user already exists
        existing_user = session.query(User).filter(User.email == user_data['email']).first()
        if existing_user:
            print(f"⚠️  User {user_data['email']} already exists, skipping")
            continue
            
        user = User(
            email=user_data['email'],
            password_hash=user_data['password_hash']
        )
        session.add(user)
        migrated_count += 1
    
    session.commit()
    print(f"✅ Migrated {migrated_count} users")
    return migrated_count

def migrate_groups(tinydb_path, session):
    """Migrate groups from TinyDB to PostgreSQL"""
    db = TinyDB(tinydb_path)
    groups_table = db.table("groups")
    
    migrated_count = 0
    for group_data in groups_table.all():
        # Check if group already exists (by name only since legacy data may not have driver)
        existing_group = session.query(Group).filter(
            Group.name == group_data['name']
        ).first()
        if existing_group:
            print(f"⚠️  Group {group_data['name']} already exists, skipping")
            continue
            
        # Convert members list to JSON string
        members_json = json.dumps(group_data.get('members', []))
        days_json = json.dumps(group_data.get('days', []))
        
        # Handle legacy data structure - provide defaults for missing fields
        group = Group(
            name=group_data['name'],
            origin=group_data.get('origin', 'Not specified'),
            destination=group_data.get('destination', 'Not specified'),
            departure_time=group_data.get('departure_time', '08:00'),
            days_of_week=days_json,
            driver=group_data.get('driver', 'TBD'),  # Default driver if not specified
            capacity=group_data.get('capacity', 4),
            members=members_json
        )
        session.add(group)
        migrated_count += 1
    
    session.commit()
    print(f"✅ Migrated {migrated_count} groups")
    return migrated_count

def migrate_on_demand_requests(tinydb_path, session):
    """Migrate on-demand requests from TinyDB to PostgreSQL"""
    db = TinyDB(tinydb_path)
    on_demand_table = db.table("on_demand_requests")
    
    migrated_count = 0
    for request_data in on_demand_table.all():
        # Handle legacy data structure - map old fields to new structure
        user_email = request_data.get('user_email', 'unknown@example.com')
        
        # Convert lat/lng to readable location if available
        origin = request_data.get('origin', 'Not specified')
        if 'origin_lat' in request_data and 'origin_lng' in request_data:
            origin = f"Lat: {request_data['origin_lat']}, Lng: {request_data['origin_lng']}"
        
        destination = request_data.get('destination', 'Not specified')
        
        # Extract date from created_at if date not available
        date_str = request_data.get('date', request_data.get('created_at', '2025-01-01'))
        if 'T' in date_str:  # ISO datetime format
            date_str = date_str.split('T')[0]  # Extract date part
        
        # Check if request already exists
        existing_request = session.query(OnDemandRequest).filter(
            OnDemandRequest.user_email == user_email,
            OnDemandRequest.origin == origin,
            OnDemandRequest.destination == destination,
            OnDemandRequest.date == date_str
        ).first()
        if existing_request:
            print(f"⚠️  On-demand request for {user_email} on {date_str} already exists, skipping")
            continue
            
        request = OnDemandRequest(
            user_email=user_email,
            origin=origin,
            destination=destination,
            date=date_str,
            preferred_driver=request_data.get('preferred_driver', request_data.get('driver'))
        )
        session.add(request)
        migrated_count += 1
    
    session.commit()
    print(f"✅ Migrated {migrated_count} on-demand requests")
    return migrated_count

def main():
    """Main migration function"""
    print("🚀 Starting TinyDB to PostgreSQL migration...")
    
    # Create database tables
    print("📋 Creating database tables...")
    create_tables()
    
    # Backup TinyDB
    tinydb_path = backup_tinydb()
    if not tinydb_path:
        print("❌ No data to migrate")
        return
    
    # Create database session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Migrate data
        users_count = migrate_users(tinydb_path, session)
        groups_count = migrate_groups(tinydb_path, session)
        requests_count = migrate_on_demand_requests(tinydb_path, session)
        
        print(f"\n🎉 Migration completed successfully!")
        print(f"   Users: {users_count}")
        print(f"   Groups: {groups_count}")
        print(f"   On-demand requests: {requests_count}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
