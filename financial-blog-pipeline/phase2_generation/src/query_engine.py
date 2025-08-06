#!/usr/bin/env python3
"""
Query engine for extracting transcripts from PostgreSQL by date, channel, and criteria
"""

import os
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class TranscriptQueryEngine:
    def __init__(self):
        self.db_connection = self._get_database_connection()
    
    def _get_database_connection(self):
        """Get PostgreSQL connection"""
        host = os.getenv('POSTGRES_HOST')
        port = os.getenv('POSTGRES_PORT')
        database = os.getenv('POSTGRES_DATABASE')
        user = os.getenv('POSTGRES_USER', 'root')
        password = os.getenv('POSTGRES_PASSWORD')
        
        conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return psycopg2.connect(conn_string)
    
    def get_transcript_by_date(self, target_date: str, channel_name: str = "游庭皓的財經皓角") -> Optional[Dict]:
        """Get transcript for specific date"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT video_id, title, channel_name, publish_date, transcript_text, 
                       duration_seconds
                FROM video_transcripts 
                WHERE DATE(publish_date) = %s AND channel_name = %s
                ORDER BY publish_date DESC
                LIMIT 1
            """, (target_date, channel_name))
            
            columns = ['video_id', 'title', 'channel_name', 'publish_date', 
                      'transcript_text', 'duration_seconds']
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            print(f"❌ Error getting transcript by date: {e}")
            return None
    
    def get_transcripts_by_range(self, start_date: str, end_date: str, 
                                channel_name: str = "于庭皓") -> List[Dict]:
        """Get transcripts for date range"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT video_id, title, channel_name, publish_date, transcript_text, 
                       duration_seconds
                FROM video_transcripts 
                WHERE DATE(publish_date) BETWEEN %s AND %s 
                AND channel_name = %s
                ORDER BY publish_date DESC
            """, (start_date, end_date, channel_name))
            
            columns = ['video_id', 'title', 'channel_name', 'publish_date', 
                      'transcript_text', 'duration_seconds']
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            print(f"❌ Error getting transcripts by range: {e}")
            return []
    
    def get_latest_transcript(self, channel_name: str = "游庭皓的財經皓角") -> Optional[Dict]:
        """Get the most recent transcript"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT video_id, title, channel_name, publish_date, transcript_text, 
                       duration_seconds
                FROM video_transcripts 
                WHERE channel_name = %s
                ORDER BY publish_date DESC
                LIMIT 1
            """, (channel_name,))
            
            columns = ['video_id', 'title', 'channel_name', 'publish_date', 
                      'transcript_text', 'duration_seconds']
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            print(f"❌ Error getting latest transcript: {e}")
            return None
    
    def get_transcript_by_video_id(self, video_id: str) -> Optional[Dict]:
        """Get transcript by specific video ID"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT video_id, title, channel_name, publish_date, transcript_text, 
                       duration_seconds, description
                FROM video_transcripts 
                WHERE video_id = %s
            """, (video_id,))
            
            columns = ['video_id', 'title', 'channel_name', 'publish_date', 
                      'transcript_text', 'duration_seconds', 'description']
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            print(f"❌ Error getting transcript by video ID: {e}")
            return None
    
    def get_unprocessed_transcripts(self, days_back: int = 7) -> List[Dict]:
        """Get recent transcripts for processing"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT video_id, title, channel_name, publish_date, 
                       transcript_text, duration_seconds
                FROM video_transcripts 
                WHERE publish_date >= NOW() - INTERVAL '%s days'
                ORDER BY publish_date DESC
            """, (days_back,))
            
            columns = ['video_id', 'title', 'channel_name', 'publish_date', 
                      'transcript_text', 'duration_seconds']
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            print(f"❌ Error getting recent transcripts: {e}")
            return []
    
    def get_transcript_stats(self) -> Dict:
        """Get basic statistics about stored transcripts"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_videos,
                    MIN(publish_date) as earliest_date,
                    MAX(publish_date) as latest_date,
                    AVG(LENGTH(transcript_text)) as avg_transcript_length,
                    channel_name
                FROM video_transcripts
                GROUP BY channel_name
                ORDER BY total_videos DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'channel_name': row[4],
                    'total_videos': row[0],
                    'earliest_date': str(row[1]),
                    'latest_date': str(row[2]),
                    'avg_transcript_length': int(row[3])
                })
            
            return {
                'channels': results,
                'total_videos': sum(r['total_videos'] for r in results)
            }
            
        except Exception as e:
            print(f"❌ Error getting transcript stats: {e}")
            return {}
    
    def mark_as_processed(self, video_id: str, blog_type: str = "traditional_chinese"):
        """Mark transcript as processed"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_blogs (
                    video_id VARCHAR(20),
                    blog_type VARCHAR(50),
                    processed_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (video_id, blog_type)
                )
            """)
            
            cursor.execute("""
                INSERT INTO processed_blogs (video_id, blog_type)
                VALUES (%s, %s)
                ON CONFLICT (video_id, blog_type) DO UPDATE
                SET processed_at = NOW()
            """, (video_id, blog_type))
            
            self.db_connection.commit()
            
        except Exception as e:
            print(f"❌ Error marking as processed: {e}")

class TranscriptManager:
    """High-level manager for transcript operations"""
    
    def __init__(self):
        self.query_engine = TranscriptQueryEngine()
    
    def get_today_transcript(self, channel_name: str = "于庭皓") -> Optional[Dict]:
        """Get today's transcript"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.query_engine.get_transcript_by_date(today, channel_name)
    
    def get_yesterday_transcript(self, channel_name: str = "于庭皓") -> Optional[Dict]:
        """Get yesterday's transcript"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        return self.query_engine.get_transcript_by_date(yesterday, channel_name)
    
    def get_weekly_transcripts(self, channel_name: str = "于庭皓") -> List[Dict]:
        """Get transcripts from last 7 days"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        return self.query_engine.get_transcripts_by_range(start_date, end_date, channel_name)

def main():
    """Test the query engine"""
    manager = TranscriptManager()
    
    print("🔍 Transcript Query Engine Test")
    print("=" * 50)
    
    # Get latest transcript
    latest = manager.query_engine.get_latest_transcript()
    if latest:
        print(f"📊 Latest transcript: {latest['title']}")
        print(f"   Date: {latest['publish_date']}")
        print(f"   Length: {len(latest['transcript_text'])} chars")
    
    # Get stats
    stats = manager.query_engine.get_transcript_stats()
    print(f"\n📈 Total videos: {stats.get('total_videos', 0)}")
    
    # Get unprocessed transcripts
    unprocessed = manager.query_engine.get_unprocessed_transcripts(days_back=7)
    print(f"📝 Unprocessed transcripts: {len(unprocessed)}")
    
    # Get today's transcript
    today = manager.get_today_transcript()
    if today:
        print(f"\n📅 Today's transcript: {today['title']}")
    else:
        print("\n📅 No transcript for today")

if __name__ == "__main__":
    main()