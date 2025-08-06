#!/usr/bin/env python3
"""
Upload YouTube transcripts to PostgreSQL (Zeabur)
Uses youtube_transcript_api to extract and store transcripts
"""

import os
import psycopg2
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_database_connection():
    """Get PostgreSQL connection using .env variables"""
    host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT')
    database = os.getenv('POSTGRES_DATABASE')
    user = os.getenv('POSTGRES_USER', 'root')
    password = os.getenv('POSTGRES_PASSWORD')
    
    if not all([host, port, database, password]):
        raise ValueError("Missing required PostgreSQL environment variables")
    
    conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return psycopg2.connect(conn_string)

def create_table():
    """Create the video_transcripts table if it doesn't exist"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
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
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_publish_date ON video_transcripts(publish_date);
        CREATE INDEX IF NOT EXISTS idx_channel_name ON video_transcripts(channel_name);
    """)
    
    conn.commit()
    conn.close()
    print("✅ Table created/verified")

def get_video_metadata(video_id):
    """Get basic video metadata (simplified)"""
    # For now, we'll use placeholder data since we only have transcript API
    # In real usage, you'd use youtube-dl or YouTube Data API v3
    return {
        'title': f'Video_{video_id}',
        'channel_name': 'Financial_Channel',
        'publish_date': datetime.now()
    }

def extract_and_upload_transcript(video_url):
    """Extract transcript and upload to PostgreSQL"""
    
    # Extract video ID from URL
    if 'watch?v=' in video_url:
        video_id = video_url.split('watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in video_url:
        video_id = video_url.split('youtu.be/')[1].split('?')[0]
    else:
        video_id = video_url
    
    print(f"🎯 Processing video: {video_id}")
    
    try:
        # Extract transcript
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=['zh-TW'])
        full_text = " ".join([segment.text for segment in transcript])
        
        # Calculate duration
        duration_seconds = int(transcript[-1].start + transcript[-1].duration)
        
        # Get metadata
        metadata = get_video_metadata(video_id)
        
        # Upload to PostgreSQL
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO video_transcripts 
            (video_id, title, channel_name, publish_date, transcript_text, duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (video_id) DO UPDATE SET
                transcript_text = EXCLUDED.transcript_text,
                updated_at = NOW()
        """, (
            video_id,
            metadata['title'],
            metadata['channel_name'],
            metadata['publish_date'],
            full_text,
            duration_seconds
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Uploaded transcript for {video_id}")
        print(f"📊 Transcript length: {len(full_text)} characters")
        print(f"⏱️ Duration: {duration_seconds}s")
        
        return {
            'video_id': video_id,
            'transcript': full_text,
            'duration': duration_seconds
        }
        
    except Exception as e:
        print(f"❌ Error processing {video_id}: {e}")
        return None

def list_uploaded_videos():
    """List all uploaded videos"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT video_id, title, channel_name, created_at, LENGTH(transcript_text) 
        FROM video_transcripts 
        ORDER BY created_at DESC
    """)
    
    videos = cursor.fetchall()
    conn.close()
    
    if videos:
        print("📋 Uploaded videos:")
        for video in videos:
            print(f"  {video[0]} - {video[1]} ({video[4]} chars)")
    else:
        print("📋 No videos uploaded yet")
    
    return videos

def get_transcript_by_video_id(video_id):
    """Retrieve transcript from database"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT transcript_text FROM video_transcripts WHERE video_id = %s",
        (video_id,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def main():
    """Main upload function"""
    
    # Check if required environment variables are set
    required_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DATABASE', 'POSTGRES_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create .env file with:")
        print("POSTGRES_HOST=your_host")
        print("POSTGRES_PORT=your_port")
        print("POSTGRES_DATABASE=your_database")
        print("POSTGRES_PASSWORD=your_password")
        print("POSTGRES_USER=root (optional, defaults to root)")
        return
    
    # Create table
    create_table()
    
    # Test with provided video
    video_url = "https://www.youtube.com/watch?v=p08_Rkh36bA"
    
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    
    result = extract_and_upload_transcript(video_url)
    
    if result:
        print("\n✅ Upload completed successfully!")
        list_uploaded_videos()

if __name__ == "__main__":
    main()