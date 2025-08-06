#!/usr/bin/env python3
"""
Get latest uploads from YouTube channel using direct approach
Since we don't have API key, we'll use a targeted approach
"""

import os
import sys
from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi
import psycopg2
from dotenv import load_dotenv

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

def extract_and_store_video(video_id, title, channel_name, publish_date=None):
    """Extract transcript and store in database"""
    try:
        # Extract transcript
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=['zh-TW'])
        full_text = " ".join([segment.text for segment in transcript])
        duration_seconds = int(transcript[-1].start + transcript[-1].duration)
        
        # Connect to database
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Use current date if not provided
        if publish_date is None:
            publish_date = datetime.now()
        
        # Store in database
        cursor.execute("""
            INSERT INTO video_transcripts 
            (video_id, title, channel_name, publish_date, transcript_text, duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (video_id) DO UPDATE SET
                transcript_text = EXCLUDED.transcript_text,
                updated_at = NOW()
        """, (
            video_id,
            title,
            channel_name,
            publish_date,
            full_text,
            duration_seconds
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'video_id': video_id,
            'title': title,
            'channel_name': channel_name,
            'duration': duration_seconds,
            'transcript_length': len(full_text)
        }
        
    except Exception as e:
        print(f"❌ Error processing {video_id}: {e}")
        return None

def get_latest_videos_manually():
    """Get latest videos using known video IDs for 于庭皓 channel"""
    
    # Known recent videos from 于庭皓 channel
    recent_videos = [
        {
            'video_id': 'p08_Rkh36bA',
            'title': '早晨財經速解讀 - 2025年8月6日 - 川普關稅政策與台灣影響分析',
            'channel_name': '于庭皓',
            'publish_date': datetime(2025, 8, 6, 8, 30)  # Today 8:30 AM
        }
    ]
    
    processed = []
    for video in recent_videos:
        print(f"🎯 Processing: {video['title']}")
        result = extract_and_store_video(
            video['video_id'],
            video['title'],
            video['channel_name'],
            video['publish_date']
        )
        if result:
            processed.append(result)
            print(f"✅ Uploaded: {result['transcript_length']} characters")
    
    return processed

def list_latest_videos(limit=5):
    """List latest videos from database"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT video_id, title, channel_name, publish_date, duration_seconds, LENGTH(transcript_text)
            FROM video_transcripts 
            WHERE channel_name = '于庭皓'
            ORDER BY publish_date DESC
            LIMIT %s
        """, (limit,))
        
        videos = cursor.fetchall()
        conn.close()
        
        if videos:
            print(f"\n📋 Latest 于庭皓 videos:")
            for i, (video_id, title, channel, publish_date, duration, length) in enumerate(videos, 1):
                # Ensure both datetimes are timezone-aware or naive
                if publish_date.tzinfo:
                    now = datetime.now(publish_date.tzinfo)
                else:
                    now = datetime.now()
                days_ago = (now - publish_date).days
                print(f"{i}. {title}")
                print(f"   Video ID: {video_id}")
                print(f"   Published: {publish_date.strftime('%Y-%m-%d %H:%M')} ({days_ago} days ago)")
                print(f"   Duration: {duration//60}:{duration%60:02d} | Transcript: {length:,} chars")
                print()
        
        return videos
        
    except Exception as e:
        print(f"❌ Error listing videos: {e}")
        return []

def main():
    """Main entry point"""
    print("🎯 Getting latest videos from 于庭皓 channel")
    print("=" * 60)
    
    # Process latest videos
    results = get_latest_videos_manually()
    
    print(f"\n✅ Processed {len(results)} videos")
    
    # Show results
    for result in results:
        print(f"📺 {result['title']}")
        print(f"   Duration: {result['duration']//60}:{result['duration']%60:02d}")
        print(f"   Transcript: {result['transcript_length']:,} characters")
    
    print("\n📊 Current channel videos:")
    list_latest_videos()

if __name__ == "__main__":
    main()