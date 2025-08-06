#!/usr/bin/env python3
"""
Main entry point for Phase 2: Enhanced blog generation with Cantonese support and image enrichment
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from src.blog_generator import FinancialBlogGenerator
from src.query_engine import TranscriptManager

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("🎯 Phase 2: Enhanced Blog Generation")
    print("🌏 Multi-language: Traditional Chinese + Cantonese")
    print("🖼️ Image enrichment with AI-generated visuals")
    print("="*70)

def generate_latest_blog():
    """Generate blog from latest transcript"""
    generator = FinancialBlogGenerator()
    manager = TranscriptManager()
    
    # Get latest transcript
    transcript = manager.get_latest_transcript(channel_name="游庭皓的財經皓角")
    if not transcript:
        print("❌ No transcripts found")
        return
    
    print(f"🎯 Processing: {transcript['title']}")
    print(f"📅 Date: {transcript['publish_date']}")
    print(f"📏 Length: {len(transcript['transcript_text'])} characters")
    
    # Generate comprehensive blog
    result = generator.generate_comprehensive_blog(transcript, include_cantonese=True)
    
    # Display results
    print(f"\n✅ Generated {len(result['generated_posts'])} blog posts:")
    for post_data in result['generated_posts']:
        lang = post_data['language']
        title = post_data['post']['title']
        print(f"   📝 {lang}: {title}")
    
    print(f"   🖼️ Generated {len(result['images'])} images")
    
    return result

def generate_blog_by_date(target_date: str):
    """Generate blog for specific date"""
    generator = FinancialBlogGenerator()
    manager = TranscriptManager()
    
    transcript = manager.query_engine.get_transcript_by_date(target_date, "游庭皓的財經皓角")
    if not transcript:
        print(f"❌ No transcript found for {target_date}")
        return
    
    print(f"🎯 Processing: {transcript['title']}")
    result = generator.generate_comprehensive_blog(transcript, include_cantonese=True)
    
    return result

def preview_blogs():
    """Preview available transcripts"""
    manager = TranscriptManager()
    
    # Get stats
    stats = manager.query_engine.get_transcript_stats()
    print(f"📊 Total videos in database: {stats.get('total_videos', 0)}")
    
    # Get latest transcript
    latest = manager.query_engine.get_latest_transcript()
    if latest:
        print(f"\n📝 Latest transcript ready:")
        print(f"   📺 Title: {latest['title']}")
        print(f"   📅 Date: {latest['publish_date']}")
        print(f"   📏 Length: {len(latest['transcript_text'])} characters")
    
    # Get recent transcripts
    recent = manager.query_engine.get_unprocessed_transcripts(days_back=7)
    if recent:
        print(f"\n🎯 Ready to process {len(recent)} recent transcripts:")
        for t in recent[:3]:  # Show first 3
            print(f"   • {t['title']} ({t['publish_date']})")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate financial blogs with multilingual support')
    parser.add_argument('--latest', action='store_true', help='Generate blog from latest transcript')
    parser.add_argument('--date', type=str, help='Generate blog for specific date (YYYY-MM-DD)')
    parser.add_argument('--preview', action='store_true', help='Preview available transcripts')
    parser.add_argument('--channel', type=str, default="游庭皓的財經皓角", help='Channel name to process')
    parser.add_argument('--no-cantonese', action='store_true', help='Skip Cantonese blog generation')
    parser.add_argument('--range', type=str, help='Date range (YYYY-MM-DD,YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.preview:
        preview_blogs()
    elif args.date:
        generate_blog_by_date(args.date)
    elif args.range:
        start_date, end_date = args.range.split(',')
        manager = TranscriptManager()
        transcripts = manager.query_engine.get_transcripts_by_range(start_date, end_date, args.channel)
        print(f"📊 Processing {len(transcripts)} transcripts in range")
    elif args.latest:
        generate_latest_blog()
    else:
        # Default: generate from latest
        generate_latest_blog()

if __name__ == "__main__":
    main()