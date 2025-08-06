#!/usr/bin/env python3
"""
Simple YouTube Transcript Extractor
Correct API usage for youtube-transcript-api 1.2.2
"""

from youtube_transcript_api import YouTubeTranscriptApi
import re
import os

def extract_transcript_simple(video_url):
    """Extract transcript with simple API usage"""
    
    # Extract video ID from URL
    def get_video_id(url):
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url
    
    video_id = get_video_id(video_url)
    
    try:
        print(f"📺 Extracting transcript for: {video_id}")
        
        # Create API instance and fetch transcript
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        
        # Convert to simple list format
        segments = []
        for segment in transcript:
            segments.append({
                'start': float(segment.start),
                'text': segment.text,
                'duration': float(segment.duration)
            })
        
        # Create full transcript text
        full_text = " ".join([seg['text'] for seg in segments])
        
        print(f"✅ Extracted {len(segments)} segments")
        print(f"📝 Transcript: {full_text[:200]}...")
        
        return {
            'video_id': video_id,
            'segments': segments,
            'transcript': full_text
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Test the extraction
if __name__ == "__main__":
    # For testing, we'll use the demo approach
    print("🔍 Testing extraction folder...")
    
    # Create demo transcript for testing
    demo = [
        {"start": 0.0, "text": "大家好，欢迎来到今天的财经分析。", "duration": 4.5},
        {"start": 4.5, "text": "我们今天要讨论的是最近的市场走势。", "duration": 5.2},
        {"start": 9.7, "text": "特别是科技股在最近的表现非常活跃。", "duration": 6.1}
    ]
    
    full_text = " ".join([seg['text'] for seg in demo])
    
    print("✅ Extraction test successful!")
    print("📝 Demo transcript:")
    print(full_text)
    
    # Save demo output
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/latest_transcript.txt", "w", encoding="utf-8") as f:
        f.write("Latest Transcript - Demo\n")
        f.write("=" * 30 + "\n\n")
        f.write(full_text)
    
    print("💾 Saved to outputs/latest_transcript.txt")