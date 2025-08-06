# 🎯 YouTube Transcript to Blog Pipeline

## Quick Start Guide

### 1. Setup (2 minutes)

```bash
# Install dependencies
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your actual values
```

### 2. Environment (.env)
```bash
# Required - Zeabur PostgreSQL
POSTGRES_HOST=hkg1.clusters.zeabur.com
POSTGRES_PORT=31546
POSTGRES_DATABASE=financial_blog
POSTGRES_PASSWORD=your_password_here
POSTGRES_USER=root

# Optional - YouTube API for channel automation
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### 3. Run the System

#### Method A: Extract by Channel ID (-chanId)
```bash
# Get latest video ID from 于庭皓 channel
python get_latest_by_channel.py -chanId UCxxxxxxxxxxxxxxxxxxx

# Get latest 5 videos from last 7 days
python get_latest_by_channel.py -chanId UCxxxxxxxxxxxxxxxxxxx 5 7

# List stored videos
python get_latest_by_channel.py --list
```

#### Method B: Extract Specific Video
```bash
# Extract and store transcript from known video
python extract_specific_video.py
# Uses: p08_Rkh36bA (today's 于庭皓 video)
```

#### Method C: Manual Extraction
```bash
# Extract from any video ID
python -c "
from youtube_transcript_api import YouTubeTranscriptApi
video_id = 'p08_Rkh36bA'
transcript = YouTubeTranscriptApi().fetch(video_id, languages=['zh-TW'])
text = ' '.join([segment.text for segment in transcript])
print(f'Extracted {len(text)} characters')
"
```

## 🏗️ Architecture

### Phase 1: Extraction → PostgreSQL
1. **Extract** Traditional Chinese transcript via youtube-transcript-api
2. **Store** in PostgreSQL with metadata (video_id, title, channel, date)
3. **Query** by date/channel for LLM processing

### Database Schema
```sql
video_transcripts (
    video_id VARCHAR(20) UNIQUE,
    title TEXT,
    channel_name TEXT,
    publish_date TIMESTAMP,
    transcript_text TEXT,
    duration_seconds INTEGER
)
```

## 🚀 Usage Examples

### Daily Workflow with Channel ID
```bash
# 于庭皓 channel: yutinghaofinance
# Channel ID: UC0lbAQVpenvfA2QqzsRtL_g

# Get latest video from 于庭皓
python get_latest_by_channel.py -chanId UC0lbAQVpenvfA2QqzsRtL_g

# Get latest 3 videos from today
python get_latest_by_channel.py -chanId UC0lbAQVpenvfA2QqzsRtL_g 3 1

# Process and store transcript
python get_latest_by_channel.py -chanId UC0lbAQVpenvfA2QqzsRtL_g 1 1

# List stored videos from 于庭皓
python get_latest_by_channel.py --list "于庭皓"
```

### Get Channel ID Guide
```bash
# ✅ 于庭皓 channel already configured
# Channel: yutinghaofinance
# Channel ID: UC0lbAQVpenvfA2QqzsRtL_g
# 
# Ready to use directly:
python get_latest_by_channel.py -chanId UC0lbAQVpenvfA2QqzsRtL_g
```

## 🔧 Testing

### Test Database Connection
```bash
python -c "
import psycopg2, os
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('✅ Database connected')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

### Test Channel ID Extraction
```bash
# Test with mock data (no API key needed)
python get_latest_by_channel.py -chanId UC_TEST_CHANNEL 3 1

# Test with YouTube API key
python get_latest_by_channel.py -chanId UC_于庭皓_REAL_CHANNEL 3 1
```

### Test Transcript Extraction
```bash
python extract_specific_video.py
# Should output: Extracted 29847 characters from p08_Rkh36bA
```

## 📊 Current Status
- **✅ Working**: Transcript extraction + PostgreSQL storage
- **✅ Tested**: p08_Rkh36bA (today's 于庭皓 video) - 33.5min, 29,847 chars
- **✅ Ready**: For Phase 2 LLM blog generation

## 🎯 Next Steps
1. **✅ 于庭皓 Channel ID**: UC0lbAQVpenvfA2QqzsRtL_g (already configured)
2. **Add YouTube API key** to .env for automated extraction
3. **Run daily**: `python get_latest_by_channel.py -chanId UC0lbAQVpenvfA2QqzsRtL_g 1 1`
4. **Connect to LLM** for blog generation

**Key Command**: `python get_latest_by_channel.py -chanId UC0lbAQVpenvfA2QqzsRtL_g`