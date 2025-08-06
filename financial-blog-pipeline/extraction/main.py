#!/usr/bin/env python3
"""
Main entry point for seamless YouTube transcript extraction and PostgreSQL upload
Simplified workflow: Get latest video from 于庭皓 channel → Extract transcript → Upload to PostgreSQL
"""

import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def check_environment():
    """Check if required environment variables are set"""
    required_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DATABASE', 'POSTGRES_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f"   {var}=your_value")
        print("\n📄 Please check .env file")
        return False
    return True

def run_latest_extraction():
    """Run the latest channel extraction with 于庭皓 channel"""
    channel_id = "UC0lbAQVpenvfA2QqzsRtL_g"
    
    print("🎯 YouTube Transcript to Blog Pipeline")
    print("=" * 50)
    print(f"Channel: 于庭皓 (yutinghaofinance)")
    print(f"Channel ID: {channel_id}")
    print("=" * 50)
    
    if not check_environment():
        return False
    
    try:
        # Run the extraction script
        cmd = [
            sys.executable, 
            os.path.join(os.path.dirname(__file__), 'get_latest_by_channel.py'),
            '-chanId',
            channel_id,
            '1',  # max videos
            '1'   # days back
        ]
        
        print("🚀 Running: get_latest_by_channel.py")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Extraction completed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Error during extraction:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Failed to run extraction: {e}")
        return False

def main():
    """Main entry point"""
    print("🎯 Starting YouTube Transcript Pipeline...")
    
    # Run the extraction for 于庭皓 channel
    success = run_latest_extraction()
    
    if success:
        print("\n🎉 Pipeline completed!")
        print("📊 Transcripts now available in PostgreSQL for LLM processing")
    else:
        print("\n❌ Pipeline failed - check configuration and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()