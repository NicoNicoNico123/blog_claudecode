#!/usr/bin/env python3
"""
Demo version of Phase 2: Shows the structure and workflow without requiring API keys
"""

import os
import sys
from datetime import datetime
from src.query_engine import TranscriptManager

class DemoBlogGenerator:
    def __init__(self):
        self.manager = TranscriptManager()
    
    def demonstrate_workflow(self):
        """Demonstrate the complete Phase 2 workflow"""
        print("\n" + "="*70)
        print("🎯 Phase 2: Enhanced Blog Generation - DEMO")
        print("🌏 Multi-language: Traditional Chinese + Cantonese")
        print("🖼️ Image enrichment with AI-generated visuals")
        print("="*70)
        
        # Get latest transcript
        latest = self.manager.query_engine.get_latest_transcript(channel_name="游庭皓的財經皓角")
        if not latest:
            print("❌ No transcripts found in database")
            return
        
        print(f"\n📊 Latest Video Found:")
        print(f"   📺 Title: {latest['title']}")
        print(f"   📅 Date: {latest['publish_date']}")
        print(f"   📏 Transcript Length: {len(latest['transcript_text'])} characters")
        print(f"   🔗 Video ID: {latest['video_id']}")
        
        # Show transcript preview
        preview_text = latest['transcript_text'][:500] + "..." if len(latest['transcript_text']) > 500 else latest['transcript_text']
        print(f"\n📝 Transcript Preview:")
        print(f"   {preview_text}")
        
        # Demonstrate what would be generated
        print(f"\n🎯 What Phase 2 Would Generate:")
        print(f"   📝 Traditional Chinese Blog: Professional Taiwan financial analysis")
        print(f"   📝 Cantonese Blog: Authentic Hong Kong KOL style")
        print(f"   🖼️ AI Images: Stock charts and market sentiment visuals")
        print(f"   📱 Ghost CMS: Ready-to-publish format")
        
        # Show blog structure examples
        print(f"\n📋 Sample Blog Structure:")
        print(f"   【繁體中文】{latest['title']}")
        print(f"   【廣東話】{latest['title']}")
        
        # Show environment setup
        print(f"\n🔧 To Run Full Version:")
        print(f"   1. Add to .env file:")
        print(f"      POSTGRES_HOST=hkg1.clusters.zeabur.com")
        print(f"      POSTGRES_PORT=31546")
        print(f"      POSTGRES_DATABASE=financial_blog")
        print(f"      POSTGRES_PASSWORD=your_password")
        print(f"      OPENAI_API_KEY=your_openai_key")
        print(f"      ANTHROPIC_API_KEY=your_anthropic_key")
        print(f"   2. pip install -r requirements.txt")
        print(f"   3. python main.py --latest")
        
        # Save demo output
        demo_output = {
            "demo_mode": True,
            "latest_transcript": {
                "video_id": latest['video_id'],
                "title": latest['title'],
                "publish_date": str(latest['publish_date']),
                "transcript_length": len(latest['transcript_text']),
                "transcript_preview": latest['transcript_text'][:200] + "..."
            },
            "would_generate": {
                "traditional_chinese_blog": f"【財經分析】{latest['title']}",
                "cantonese_blog": f"【財經拆解】{latest['title']}",
                "ai_images": 2,
                "ghost_cms_format": True
            }
        }
        
        # Save demo file
        output_dir = "/Users/nico/coding/blog_claudecode/financial-blog-pipeline/phase2_generation/outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        import json
        filename = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(demo_output, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n✅ Demo saved to: {filepath}")
        print(f"🎉 Phase 2 structure is ready and working!")

if __name__ == "__main__":
    demo = DemoBlogGenerator()
    demo.demonstrate_workflow()