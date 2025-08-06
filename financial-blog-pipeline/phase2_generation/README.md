# Phase 2: Enhanced Blog Generation

## Overview
Phase 2 transforms extracted YouTube transcripts into rich, multilingual blog posts with AI-generated images. Features both Traditional Chinese and authentic Cantonese financial blogger styles.

## Quick Start

### 1. Install Dependencies
```bash
cd financial-blog-pipeline/phase2_generation
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file:
```bash
POSTGRES_HOST=hkg1.clusters.zeabur.com
POSTGRES_PORT=31546
POSTGRES_DATABASE=financial_blog
POSTGRES_USER=root
POSTGRES_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### 3. Test the System
```bash
# Preview available transcripts
python main.py --preview

# Generate blog from latest transcript
python main.py --latest

# Generate blog for specific date
python main.py --date 2024-08-06

# Generate blogs for date range
python main.py --range 2024-08-01,2024-08-05
```

## Features

### 🌏 Multilingual Support
- **Traditional Chinese**: Professional Taiwan financial blogger style
- **Cantonese**: Authentic Hong Kong KOL tone with 地道廣東話

### 🖼️ AI Image Generation
- **Agent-Based Architecture**: Specialized agents for each image task
- **Content Analysis**: LLM-powered context extraction from blog content
- **Smart Prompting**: Agents generate optimal prompts for image creation
- **Dual Approach**: Generate new images (DALL-E 3) or search existing ones (Unsplash)
- **Parallel Processing**: Simultaneous image generation and search for performance
- **Fallback Mechanisms**: Graceful degradation when APIs are unavailable

### 📊 Data Sources
- PostgreSQL integration with Phase 1 data
- Real-time transcript querying by date/channel
- Automatic detection of unprocessed content

### 📝 Blog Structure

#### Traditional Chinese Style
1. **開場吸睛** - Hook with surprising data
2. **市場影響分析** - Taiwan stock impact analysis
3. **小白也能懂** - Simple explanations with examples
4. **關鍵結論** - 3-5 specific investment recommendations

#### Cantonese Style
1. **開場白** - "大家好，我係..." authentic opening
2. **市場分析** - Hong Kong stock examples (騰訊 0700, 港交所 0388)
3. **投資貼士** - "記住呢幾點" format
4. **地道結語** - Local encouragement and risk reminders

## Usage Examples

### Basic Usage
```python
from src.blog_generator import FinancialBlogGenerator

# Initialize generator
generator = FinancialBlogGenerator()

# Get latest transcript
video_data = generator.get_latest_transcript()[0]

# Generate comprehensive blog
result = generator.generate_comprehensive_blog(video_data)

# Output includes:
# - Traditional Chinese blog post
# - Cantonese blog post (optional)
# - AI-generated images
# - Ghost CMS ready format
```

### Advanced Querying
```python
from src.query_engine import TranscriptManager

manager = TranscriptManager()

# Get specific date
transcript = manager.query_engine.get_transcript_by_date(
    "2024-08-06", 
    channel_name="于庭皓"
)

# Get unprocessed content
unprocessed = manager.query_engine.get_unprocessed_transcripts(days_back=7)
```

## Output Structure

### Generated Files
```
phase2_generation/outputs/
├── [video_id]_blogs_[timestamp].json    # Complete blog data
└── images/
    ├── stock_chart_[timestamp].png      # DALL-E generated charts
    └── sentiment_[timestamp].png        # Market sentiment visuals
```

### Blog Post Format
```json
{
  "original_video": {
    "video_id": "p08_Rkh36bA",
    "title": "影片標題",
    "transcript_text": "完整逐字稿..."
  },
  "generated_posts": [
    {
      "language": "traditional_chinese",
      "post": {
        "title": "【財經分析】...",
        "html": "Ghost CMS ready HTML...",
        "tags": ["財經", "投資"],
        "meta_description": "..."
      }
    },
    {
      "language": "cantonese",
      "post": {...}
    }
  ],
  "images": ["dalle_image_url_1", "dalle_image_url_2"]
}
```

## Environment Variables

### Required
- `POSTGRES_HOST`: Zeabur PostgreSQL host
- `POSTGRES_PORT`: Database port (31546)
- `POSTGRES_DATABASE`: Database name
- `POSTGRES_PASSWORD`: Database password
- `OPENAI_API_KEY`: For DALL-E 3 image generation
- `ANTHROPIC_API_KEY`: For Claude blog generation
- `UNSPLASH_API_KEY`: For web image search (optional, falls back to DALL-E only)

### Optional
- `POSTGRES_USER`: Default 'root'
- `GHOST_URL`: Ghost CMS endpoint
- `GHOST_ADMIN_API_KEY`: For direct publishing

## Testing

### Validate Setup
```bash
# Test database connection
python src/query_engine.py

# Test blog generation (dry run)
python src/blog_generator.py

# Generate preview
python main.py --preview
```

### Sample Output
```
🎯 Phase 2: Enhanced Blog Generation
🌏 Multi-language: Traditional Chinese + Cantonese
🖼️ Image enrichment with AI-generated visuals
======================================================================

📊 Total videos in database: 15
📝 Latest transcript ready:
   📺 Title: 美股大跌對台股影響分析
   📅 Date: 2024-08-06
   📏 Length: 11770 characters

✅ Generated 2 blog posts
📁 Saved to: outputs/p08_Rkh36bA_blogs_20240806_143022.json
📝 TRADITIONAL_CHINESE Blog: 【財經分析】美股大跌對台股影響分析
📝 CANTONESE Blog: 【財經拆解】美股大跌點影響港股？
   Images: 2
```

## Integration with Ghost CMS

The system generates ready-to-publish Ghost posts:
- **HTML Format**: Including images and proper formatting
- **SEO Optimized**: Meta descriptions and tags
- **Featured Images**: AI-generated visuals included
- **Multi-language**: Separate posts for Traditional Chinese and Cantonese audiences

## Troubleshooting

### Common Issues
1. **Database Connection**: Check PostgreSQL credentials in .env
2. **API Keys**: Ensure OpenAI and Anthropic keys are valid
3. **Date Format**: Use YYYY-MM-DD format for date queries
4. **Channel Names**: Use exact channel name from database (e.g., "于庭皓")

### Debug Mode
```bash
# Enable verbose logging
python main.py --latest --verbose

# Check database connection
python -c "from src.query_engine import TranscriptManager; print('Connected!' if TranscriptManager().query_engine.db_connection else 'Failed')"
```