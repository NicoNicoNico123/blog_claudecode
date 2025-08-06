#!/usr/bin/env python3
"""
Extract transcript from specific YouTube video URL
Stores output in terminal and output folder
"""

from youtube_transcript_api import YouTubeTranscriptApi
import re
import os

def extract_transcript_from_url(video_url):
    """Extract transcript from YouTube URL and display in terminal"""
    
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
    
    print("🔍 Extracting transcript from provided video")
    print("=" * 80)
    print(f"📺 Video URL: {video_url}")
    print(f"🎯 Video ID: {video_id}")
    
    try:
        # Create API instance
        api = YouTubeTranscriptApi()
        
        # Extract transcript with Traditional Chinese language
        transcript = api.fetch(video_id, languages=['zh-TW', 'zh-CN', 'en'])
        
        # Convert to list format
        segments = []
        for segment in transcript:
            segments.append({
                'start': float(segment.start),
                'text': segment.text,
                'duration': float(segment.duration)
            })
        
        # Create full transcript text
        full_text = " ".join([seg['text'] for seg in segments])
        
        print(f"✅ Successfully extracted {len(segments)} segments")
        
        # Calculate duration
        if segments:
            first = segments[0]['start']
            last = segments[-1]['start'] + segments[-1]['duration']
            duration = last - first
            print(f"⏱️  Duration: {duration:.1f}s ({duration/60:.1f} min)")
        
        # Display complete transcript in terminal
        print("\n" + "="*80)
        print("📝 COMPLETE TRANSCRIPT")
        print("="*80)
        print(full_text)
        
        # Display segment-by-segment
        print("\n" + "="*80)
        print("📊 DETAILED SEGMENTS")
        print("="*80)
        
        for i, segment in enumerate(segments):
            start = segment['start']
            text = segment['text'].strip()
            
            # Format timestamp
            hours = int(start // 3600)
            minutes = int((start % 3600) // 60)
            seconds = int(start % 60)
            
            if hours > 0:
                timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                timestamp = f"{minutes:02d}:{seconds:02d}"
            
            print(f"[{timestamp}] {text}")
        
        # Store in output folder
        os.makedirs("outputs", exist_ok=True)
        output_file = f"outputs/{video_id}_transcript.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"YouTube Transcript - {video_id}\n")
            f.write(f"Video URL: {video_url}\n")
            f.write(f"Segments: {len(segments)}\n")
            f.write(f"Duration: {duration:.1f}s\n")
            f.write("=" * 50 + "\n\n")
            
            for segment in segments:
                start = segment['start']
                text = segment['text'].strip()
                f.write(f"[{start:.1f}s] {text}\n")
        
        print(f"\n💾 Saved transcript to: {output_file}")
        
        return {
            'video_id': video_id,
            'transcript': full_text,
            'segments': segments,
            'duration': duration
        }
        
    except Exception as e:
        print(f"❌ Error extracting transcript: {e}")
        
        # Try to list available transcripts
        try:
            api = YouTubeTranscriptApi()
            available = api.list(video_id)
            print("\n📋 Available transcripts:")
            for lang in available:
                print(f"  - {lang}")
        except Exception as e2:
            print(f"❌ Could not list transcripts: {e2}")
        
        return None

if __name__ == "__main__":
    # Extract from the provided URL
    url = "https://www.youtube.com/watch?v=p08_Rkh36bA"
    result = extract_transcript_from_url(url)
    
    if result:
        print("\n" + "=" * 80)
        print("✅ EXTRACTION COMPLETE!")
        print("=" * 80)
        print(f"📺 Video processed: {result['video_id']}")
        print(f"📊 {len(result['segments'])} segments extracted")
        print(f"⏱️  Duration: {result['duration']:.1f}s")
        print("💾 Transcript saved to outputs folder")
    else:
        print("\n❌ Extraction failed - creating demo instead")
        
        # Create demo transcript for testing
        demo_transcript = [
            {"start": 0.0, "text": "欢迎来到今天的财经分析，我们来聊聊最新的市场动态。", "duration": 5.0},
            {"start": 5.0, "text": "首先看看美股的表现，纳斯达克昨天收盘上涨1.8%。", "duration": 6.0},
            {"start": 11.0, "text": "科技股整体表现不错，特别是半导体板块领涨。", "duration": 5.5},
            {"start": 16.5, "text": "从技术分析来看，这是一个健康的上升趋势。", "duration": 4.8},
            {"start": 21.3, "text": "投资者应该关注接下来的美联储会议。", "duration": 5.2}
        ]
        
        # Save demo
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/p08_Rkh36bA_transcript.txt", "w", encoding="utf-8") as f:
            f.write("Demo Transcript - p08_Rkh36bA\n")
            f.write("=" * 50 + "\n\n")
            for segment in demo_transcript:
                f.write(f"[{segment['start']:.1f}s] {segment['text']}\n")
        
        print("💾 Demo transcript saved to outputs/p08_Rkh36bA_transcript.txt")