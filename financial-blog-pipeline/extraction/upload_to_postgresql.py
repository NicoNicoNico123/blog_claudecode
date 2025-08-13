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
    user = os.getenv('POSTGRES_USERNAME', os.getenv('POSTGRES_USER', 'root'))
    password = os.getenv('POSTGRES_PASSWORD')
    
    if not all([host, port, database, password]):
        raise ValueError("Missing required PostgreSQL environment variables")
    
    conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return psycopg2.connect(conn_string)

def ensure_target_table():
    """Verify that target table 'blog' exists. Do not attempt to create/alter it."""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'blog'")
        exists = cursor.fetchone() is not None
        conn.close()
        if exists:
            print("✅ Found existing table: blog")
        else:
            print("❌ Table 'blog' not found. Please create it before running this script.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to verify target table 'blog': {e}")
        sys.exit(1)

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

        # Dynamic column mapping
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'blog'")
        cols = {name for (name,) in cursor.fetchall()}

        def pick(*candidates):
            for c in candidates:
                if c in cols:
                    return c
            return None

        video_col = pick('video_id', 'videoid', 'videoId')
        title_col = pick('title')
        channel_id_col = pick('channelid', 'channel_id', 'channelId')
        channel_name_col = pick('channel_name', 'channelname', 'channel')
        publish_col = pick('publish_date', 'publishdate', 'published_at', 'publishedat')
        transcript_col = pick('transcript_text', 'transcripttext', 'transcript')
        duration_col = pick('duration_seconds', 'durationseconds', 'duration')

        values_map = {}
        if video_col: values_map[video_col] = video_id
        if title_col: values_map[title_col] = metadata['title']
        if channel_id_col: values_map[channel_id_col] = os.getenv('YOUTUBE_CHANNEL_ID') or 'unknown'
        if channel_name_col: values_map[channel_name_col] = metadata['channel_name']
        if publish_col: values_map[publish_col] = metadata['publish_date']
        if transcript_col: values_map[transcript_col] = full_text
        if duration_col: values_map[duration_col] = duration_seconds

        # Try UPDATE by video id first
        if video_col and transcript_col:
            set_cols = [c for c in values_map.keys() if c != video_col]
            if set_cols:
                set_clause = ", ".join([f"{c} = %s" for c in set_cols])
                update_sql = f"UPDATE blog SET {set_clause} WHERE {video_col} = %s"
                params = [values_map[c] for c in set_cols] + [values_map[video_col]]
                cursor.execute(update_sql, params)
                if cursor.rowcount == 0:
                    # INSERT
                    insert_cols = list(values_map.keys())
                    placeholders = ", ".join(["%s"] * len(insert_cols))
                    insert_sql = f"INSERT INTO blog ({', '.join(insert_cols)}) VALUES ({placeholders})"
                    cursor.execute(insert_sql, [values_map[c] for c in insert_cols])
        else:
            # Fallback: direct INSERT with available columns
            insert_cols = list(values_map.keys())
            placeholders = ", ".join(["%s"] * len(insert_cols))
            insert_sql = f"INSERT INTO blog ({', '.join(insert_cols)}) VALUES ({placeholders})"
            cursor.execute(insert_sql, [values_map[c] for c in insert_cols])
        
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
    
    # Dynamic select
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'blog'")
    cols = {name for (name,) in cursor.fetchall()}
    def pick(*candidates):
        for c in candidates:
            if c in cols:
                return c
        return None
    video_col = pick('video_id', 'videoid', 'videoId') or 'NULL as video_id'
    title_col = pick('title') or 'NULL as title'
    channel_col = pick('channel_name', 'channelname', 'channel') or 'NULL as channel_name'
    created_col = pick('created_at', 'createdat') or 'NOW() as created_at'
    transcript_col = pick('transcript_text', 'transcripttext', 'transcript')
    length_expr = f"LENGTH({transcript_col})" if transcript_col else '0'
    order_col = created_col.split()[0] if ' as ' in created_col else created_col
    sql = f"SELECT {video_col}, {title_col}, {channel_col}, {created_col}, {length_expr} FROM blog ORDER BY {order_col} DESC"
    cursor.execute(sql)
    
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
    
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'blog'")
    cols = {name for (name,) in cursor.fetchall()}
    def pick(*candidates):
        for c in candidates:
            if c in cols:
                return c
        return None
    transcript_col = pick('transcript_text', 'transcripttext', 'transcript') or 'transcript_text'
    video_col = pick('video_id', 'videoid', 'videoId') or 'video_id'
    cursor.execute(
        f"SELECT {transcript_col} FROM blog WHERE {video_col} = %s",
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
    
    # Ensure target table exists
    ensure_target_table()
    
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