#!/usr/bin/env python3
"""
Get latest videos by channel ID using YouTube Data API v3
Extract transcripts from the most recent videos in a channel
"""

import os
import sys
from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from dotenv import load_dotenv
import psycopg2

# Load environment variables
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

def get_youtube_service():
    """Create YouTube API service"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key or api_key == 'your_youtube_api_key_here':
        return None
    
    return build('youtube', 'v3', developerKey=api_key)

def get_channel_videos(channel_id, max_results=10, days_back=7):
    """
    Get latest videos from a channel
    
    Args:
        channel_id: YouTube channel ID (starts with UC...)
        max_results: Maximum number of videos to return
        days_back: Look back this many days
    """
    youtube = get_youtube_service()
    
    if not youtube:
        print("⚠️ YouTube API key not configured. Using mock data for demonstration.")
        return get_mock_channel_videos(channel_id, max_results, days_back)
    
    # Calculate date range
    published_after = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    try:
        # Get videos from channel
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=max_results,
            order="date",
            type="video",
            publishedAfter=published_after
        )
        
        response = request.execute()
        videos = []
        
        for item in response.get('items', []):
            video_data = {
                'video_id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'channel_name': item['snippet']['channelTitle'],
                'publish_date': item['snippet']['publishedAt'],
                'description': item['snippet']['description']
            }
            videos.append(video_data)
            
        return videos
        
    except Exception as e:
        print(f"❌ Error getting channel videos: {e}")
        return []

def get_mock_channel_videos(channel_id, max_results=5, days_back=7):
    """Mock channel videos for demonstration when API key is not available"""
    print(f"📊 Mock data for channel: {channel_id}")
    
    mock_videos = [
        {
            'video_id': 'p08_Rkh36bA',
            'title': '【財經分析】2024年投資策略大解析',
            'channel_name': '于庭皓',
            'publish_date': '2024-12-30T10:00:00Z',
            'description': '深入分析2024年的投資機會和風險'
        },
        {
            'video_id': 'VIDEO_ID_2',
            'title': '科技股投資指南：AI浪潮下的機會',
            'channel_name': '于庭皓',
            'publish_date': '2024-12-28T09:30:00Z',
            'description': '探討AI技術發展對科技股的影響'
        },
        {
            'video_id': 'VIDEO_ID_3',
            'title': '房地產市場最新趨勢分析',
            'channel_name': '于庭皓',
            'publish_date': '2024-12-25T14:00:00Z',
            'description': '2024年房地產投資策略'
        }
    ]
    
    return mock_videos[:max_results]

def extract_transcript(video_id):
    """Extract Traditional Chinese transcript"""
    try:
        # Handle mock video case
        if video_id in ['VIDEO_ID_2', 'VIDEO_ID_3']:
            return {
                'transcript': f'這是{video_id}的模擬字幕內容，用於測試系統功能。包含一些財經術語如股票、投資、風險管理等。',
                'duration': 1800
            }
        
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=['zh-TW'])
        full_text = " ".join([segment.text for segment in transcript])
        duration_seconds = int(transcript[-1].start + transcript[-1].duration)
        return {
            'transcript': full_text,
            'duration': duration_seconds
        }
    except Exception as e:
        print(f"❌ Failed to extract transcript for {video_id}: {e}")
        return None

def upload_transcript_to_postgresql(video_data, transcript_data):
    """Upload transcript to PostgreSQL"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Parse publish date
        publish_dt = datetime.fromisoformat(video_data['publish_date'].replace('Z', '+00:00'))
        
        cursor.execute("""
            INSERT INTO video_transcripts 
            (video_id, title, channel_name, publish_date, transcript_text, duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (video_id) DO UPDATE SET
                transcript_text = EXCLUDED.transcript_text,
                updated_at = NOW()
        """, (
            video_data['video_id'],
            video_data['title'],
            video_data['channel_name'],
            publish_dt,
            transcript_data['transcript'],
            transcript_data['duration']
        ))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to upload transcript: {e}")
        return False

def process_channel_videos(channel_id, max_videos=5, days_back=7):
    """
    Process latest videos from a channel
    
    Args:
        channel_id: YouTube channel ID
        max_videos: Maximum videos to process
        days_back: Days to look back
    """
    print(f"🎯 Processing channel: {channel_id}")
    print(f"📅 Looking back {days_back} days")
    
    # Get latest videos
    videos = get_channel_videos(channel_id, max_videos, days_back)
    
    if not videos:
        print("❌ No videos found")
        return
    
    print(f"📺 Found {len(videos)} videos")
    
    processed_count = 0
    for video in videos:
        print(f"\n🎥 Processing: {video['title']}")
        print(f"🔗 Video ID: {video['video_id']}")
        
        # Check if already exists
        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM video_transcripts WHERE video_id = %s", (video['video_id'],))
            exists = cursor.fetchone()[0] > 0
            conn.close()
            
            if exists:
                print("✅ Already exists, skipping")
                continue
        except Exception as e:
            print(f"⚠️ Error checking existence: {e}")
        
        # Extract transcript
        transcript = extract_transcript(video['video_id'])
        if not transcript:
            continue
        
        # Upload to PostgreSQL
        if upload_transcript_to_postgresql(video, transcript):
            processed_count += 1
            print(f"✅ Uploaded ({processed_count}/{len(videos)})")
            print(f"📊 Transcript: {len(transcript['transcript'])} characters")
            print(f"⏱️ Duration: {transcript['duration']}s")
        else:
            print("❌ Upload failed")
    
    print(f"\n🎉 Processed {processed_count} videos from channel")

def list_videos_by_channel(channel_name=None, limit=10):
    """List videos by channel name"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        if channel_name:
            cursor.execute("""
                SELECT video_id, title, channel_name, publish_date, duration_seconds, LENGTH(transcript_text)
                FROM video_transcripts 
                WHERE channel_name = %s
                ORDER BY publish_date DESC
                LIMIT %s
            """, (channel_name, limit))
        else:
            cursor.execute("""
                SELECT video_id, title, channel_name, publish_date, duration_seconds, LENGTH(transcript_text)
                FROM video_transcripts 
                ORDER BY publish_date DESC
                LIMIT %s
            """, (limit,))
        
        videos = cursor.fetchall()
        conn.close()
        
        if videos:
            print(f"\n📋 Videos{' for channel: ' + channel_name if channel_name else ''}:")
            for i, (video_id, title, channel, publish_date, duration, length) in enumerate(videos, 1):
                print(f"{i}. {video_id} - {title}")
                print(f"   Channel: {channel} | Published: {publish_date.strftime('%Y-%m-%d')}")
                print(f"   Duration: {duration}s | Transcript: {length} chars")
                print()
        else:
            print("📋 No videos found")
            
        return videos
        
    except Exception as e:
        print(f"❌ Error listing videos: {e}")
        return []

def main():
    """Main entry point"""
    
    # Check environment (only require PostgreSQL, YouTube API is optional)
    required_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DATABASE', 'POSTGRES_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create .env file with:")
        print("POSTGRES_HOST=your_host")
        print("POSTGRES_PORT=your_port")
        print("POSTGRES_DATABASE=your_database")
        print("POSTGRES_PASSWORD=your_password")
        print("YOUTUBE_API_KEY=your_youtube_api_key (optional)")
        return
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python get_latest_by_channel.py -chanId <channel_id> [max_videos] [days_back]")
        print("  python get_latest_by_channel.py --list [channel_name]")
        print("")
        print("Examples:")
        print("  python get_latest_by_channel.py -chanId UC0lbAQVpenvfA2QqzsRtL_g")
        print("  python get_latest_by_channel.py -chanId UC0lbAQVpenvfA2QqzsRtL_g 5 7")
        print("  python get_latest_by_channel.py --list")
        print("  python get_latest_by_channel.py --list '于庭皓'")
        return
    
    if sys.argv[1] == '--list':
        channel_name = sys.argv[2] if len(sys.argv) > 2 else None
        list_videos_by_channel(channel_name)
    elif sys.argv[1] == '-chanId':
        if len(sys.argv) < 3:
            print("❌ -chanId requires a channel ID parameter")
            return
        
        channel_id = sys.argv[2]
        max_videos = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        days_back = int(sys.argv[4]) if len(sys.argv) > 4 else 7
        
        process_channel_videos(channel_id, max_videos, days_back)
    else:
        # Support direct channel ID for backward compatibility
        channel_id = sys.argv[1]
        max_videos = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        days_back = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        
        process_channel_videos(channel_id, max_videos, days_back)

if __name__ == "__main__":
    main()