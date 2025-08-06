# Phase 3: Ghost Blog Formatting and Uploading

This phase takes LLM-generated blog posts from Phase 4 and formats them into Ghost CMS compatible format, then uploads them to your Ghost blog.

## Overview

Phase 3 bridges the gap between AI-generated content and live blog posts by:
1. **Formatting** raw LLM output into Ghost-compatible JSON format
2. **Adding SEO metadata** like titles, descriptions, and tags
3. **Uploading** directly to Ghost CMS as drafts or published posts
4. **Managing** images, tags, and post organization

## Directory Structure

```
phase3_ghost_formatting/
├── main.py                 # Main orchestration script
├── ghost_formatter.py      # Content formatting module
├── ghost_uploader.py       # Ghost CMS upload module
├── requirements.txt        # Python dependencies
├── README.md              # This documentation
├── outputs/               # Formatted posts and logs
└── tests/                 # Unit tests
```

## Setup

### 1. Install Dependencies

```bash
cd financial-blog-pipeline/phase3_ghost_formatting
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root or ensure these variables are set:

```bash
# Ghost CMS Configuration
GHOST_URL="https://your-ghost-blog.com"
GHOST_ADMIN_API_KEY="your-admin-api-key-from-ghost"
```

**Note**: The Ghost Admin API key should be in format: `{id}:{secret}` (found in Ghost admin → Integrations → Add custom integration)

### 3. Validate Setup

```bash
# Test environment variables
python main.py --validate

# Test Ghost connection
python main.py --test-connection
```

## Usage

### Process Single Blog Draft

```bash
# Format and save as draft
python main.py --single ../phase4_generation/outputs/blog_drafts/my_post.json

# Format and publish immediately
python main.py --single ../phase4_generation/outputs/blog_drafts/my_post.json --publish
```

### Process Multiple Drafts (Batch)

```bash
# Process all drafts in directory as drafts
python main.py --batch ../phase4_generation/outputs/blog_drafts/

# Process and publish all drafts
python main.py --batch ../phase4_generation/outputs/blog_drafts/ --publish
```

### Default Processing

If no arguments are provided, Phase 3 will automatically look for drafts in:
```
../phase4_generation/outputs/blog_drafts/
```

## Input Format

Blog drafts should be JSON files with this structure:

```json
{
  "title": "股票分析：今日市場回顧",
  "content": "# 市場概況\n今日台灣加權指數...",
  "tags": ["股市分析", "投資策略"],
  "feature_image": "https://example.com/image.jpg",
  "excerpt": "今日市場簡要回顧..."
}
```

## Output Format

Phase 3 creates Ghost-compatible JSON files in `outputs/`:

```json
{
  "posts": [{
    "title": "股票分析：今日市場回顧",
    "slug": "股票分析今日市場回顧",
    "html": "<h1>市場概況</h1>...",
    "mobiledoc": {...},
    "tags": [{"name": "股市分析", "slug": "股市分析"}],
    "status": "draft",
    "custom_excerpt": "今日市場簡要回顧...",
    "meta_title": "股票分析：今日市場回顧",
    "meta_description": "今日市場簡要回顧..."
  }]
}
```

## Features

### Content Formatting
- ✅ Markdown to HTML conversion
- ✅ SEO meta tags generation
- ✅ URL slug generation
- ✅ Tag extraction and management
- ✅ Feature image handling
- ✅ Excerpt generation

### Ghost Integration
- ✅ Direct upload via Ghost Admin API
- ✅ Draft/publish control
- ✅ Image upload support
- ✅ Tag creation and management
- ✅ Connection testing
- ✅ Error handling and logging

### SEO Optimization
- ✅ Meta title and description
- ✅ Open Graph tags
- ✅ Twitter Card tags
- ✅ Structured data
- ✅ Canonical URLs

## Examples

### Basic Usage

```python
from ghost_formatter import GhostFormatter
from ghost_uploader import GhostUploader

# Format content
formatter = GhostFormatter()
ghost_post = formatter.format_blog_post(
    title="我的投資分析",
    content="# 市場分析\n今日股市表現...",
    tags=[{"name": "投資", "slug": "investment"}]
)

# Upload to Ghost
uploader = GhostUploader()
uploader.create_post(ghost_post, publish=True)
```

### Batch Processing Script

```python
import os
from main import Phase3Orchestrator

orchestrator = Phase3Orchestrator()
orchestrator.initialize_uploader()

# Process all drafts
results = orchestrator.process_batch(
    "../phase4_generation/outputs/blog_drafts/",
    publish=False  # Save as drafts
)

print(f"Processed {results['total_processed']} posts")
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check GHOST_URL format (include https://)
   - Verify GHOST_ADMIN_API_KEY format (should be id:secret)
   - Ensure Ghost is accessible from your network

2. **Permission Errors**
   - Verify Admin API key has proper permissions
   - Check if user has admin/editor role

3. **Tag Issues**
   - Ensure tags don't exceed Ghost limits
   - Check for duplicate tag names

### Debug Commands

```bash
# Check environment
python main.py --validate

# Test Ghost connection
python main.py --test-connection

# Verbose logging
python main.py --single my_post.json --log-level DEBUG
```

### Logs

All processing logs are saved in:
- `outputs/phase3.log` - Detailed logs
- `outputs/batch_results_*.json` - Batch processing results
- `outputs/upload_log_*.json` - Individual upload logs

## Integration with Pipeline

Phase 3 expects input from:
- **Phase 4**: LLM-generated blog drafts at `../phase4_generation/outputs/blog_drafts/`

Phase 3 outputs to:
- **Ghost CMS**: Live blog posts
- **Local logs**: Processing results and logs in `outputs/`

## Next Steps

After Phase 3 completes:
1. Review uploaded posts in Ghost admin
2. Edit drafts if needed
3. Publish or schedule published posts
4. Monitor engagement metrics in Ghost analytics