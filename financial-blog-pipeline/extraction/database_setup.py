#!/usr/bin/env python3
"""
Database setup script for PostgreSQL
Creates table and indexes for transcript storage
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_database_connection():
    """Get PostgreSQL connection using .env variables"""
    host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT')
    database = os.getenv('POSTGRES_DATABASE')
    user = os.getenv('POSTGRES_USERNAME', os.getenv('POSTGRES_USER', 'root'))
    password = os.getenv('POSTGRES_PASSWORD')
    
    if not all([host, port, database, password]):
        raise ValueError("Missing required PostgreSQL environment variables")
    
    conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return psycopg2.connect(conn_string)

def setup_database():
    """Create database table for transcript storage"""
    
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_transcripts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            video_id VARCHAR(20) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            publish_date TIMESTAMP WITH TIME ZONE,
            transcript_text TEXT NOT NULL,
            duration_seconds INTEGER,
            language VARCHAR(10) DEFAULT 'zh-TW',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_video_id ON video_transcripts(video_id);
        CREATE INDEX IF NOT EXISTS idx_publish_date ON video_transcripts(publish_date);
        CREATE INDEX IF NOT EXISTS idx_channel_name ON video_transcripts(channel_name);
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Database setup complete!")
    print("📊 Table 'video_transcripts' created with indexes")

def check_connection():
    """Test database connection"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM video_transcripts")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        print("✅ Database connection successful!")
        print(f"📊 PostgreSQL version: {version.split()[1]}")
        print(f"📊 Total transcripts: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    try:
        setup_database()
        check_connection()
    except ValueError as e:
        print(f"❌ {e}")
        print("Please create .env file with:")
        print("POSTGRES_HOST=your_host")
        print("POSTGRES_PORT=your_port")
        print("POSTGRES_DATABASE=your_database")
        print("POSTGRES_PASSWORD=your_password")
        print("POSTGRES_USER=root (optional, defaults to root)")