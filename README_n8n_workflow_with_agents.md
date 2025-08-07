# YouTube to Blog Pipeline - n8n Workflow with AI Agents

This repository contains a comprehensive n8n workflow that automates the process of converting YouTube financial education videos into blog posts. The workflow uses AI Agent nodes to orchestrate specialized agents for each task, replacing the previous Execute Command approach.

## Workflow Overview

The pipeline processes videos from 于庭皓's YouTube channel and generates Traditional Chinese blog posts with relevant images.

### Architecture

```
Master Orchestrator Workflow with AI Agents
├── YouTube Transcript Extractor Agent
├── Blog Generator Agent
├── Image Context Analyzer Agent
├── Image Prompt Generator Agent
├── Image Generator Agent (DALL-E)
├── Image Search Agent (Unsplash)
├── Cloudinary Image Upload Agent
├── Content Formatter Agent
└── Publisher Agent
```

## Workflow Steps

1. **Cron Trigger** - Runs daily at 9 AM
2. **YouTube Channel Info** - Gets channel information
3. **Latest Video** - Fetches the latest video from the channel
4. **Transcript Check** - Checks if transcript already exists
5. **Transcript Extraction** - Extracts video transcript using AI Agent
6. **Store Transcript** - Saves transcript to PostgreSQL
7. **Blog Generation** - Creates Traditional Chinese blog post using AI Agent
8. **Content Analysis** - Analyzes blog content to identify image contexts using AI Agent
9. **Prompt Generation** - Creates appropriate prompts for image generation/search using AI Agent
10. **Image Generation** - Generates charts and graphs using DALL-E
11. **Image Search** - Finds relevant photos using Unsplash
12. **Cloudinary Upload** - Uploads all images to Cloudinary for reliable hosting
13. **Content Formatting** - Formats blog post with Cloudinary image URLs using AI Agent
14. **Publication** - Publishes blog post to Ghost CMS
15. **Logging** - Logs completion status to PostgreSQL

## Agent Descriptions

### YouTube Transcript Extractor Agent
- Fetches the latest video from a specified YouTube channel
- Extracts the video transcript using YouTube Transcript API
- Stores the transcript in PostgreSQL

### Blog Generator Agent
- Retrieves transcript from PostgreSQL
- Generates blog posts in Traditional Chinese using Claude
- Creates SEO-optimized content with financial insights

### Image Context Analyzer Agent
- Analyzes blog content to identify key topics
- Determines which sentences/concepts need visual representation
- Categorizes image requirements (charts, photos, illustrations)

### Image Prompt Generator Agent
- Creates specific prompts for each image context
- Determines whether to generate or search for images
- Optimizes prompts for DALL-E or search engines

### Image Generator Agent
- Uses DALL-E to create custom financial charts and graphs
- Generates images based on the generated prompts
- Returns image URLs for inclusion in blog posts

### Image Search Agent
- Searches Unsplash for relevant photos
- Uses search prompts to find appropriate images
- Returns image URLs for inclusion in blog posts

### Cloudinary Upload Agent
- Uploads generated and searched images to Cloudinary
- Retrieves Cloudinary URLs for reliable image hosting
- Passes Cloudinary URLs to the Content Formatter Agent

### Content Formatter Agent
- Combines blog content with Cloudinary image URLs
- Formats content for Ghost CMS
- Creates proper JSON structure with image placements

### Publisher Agent
- Publishes formatted content to Ghost CMS
- Logs publication status

## Prerequisites

1. n8n installation
2. PostgreSQL database
3. API keys for:
   - Anthropic (Claude)
   - OpenAI (DALL-E)
   - Unsplash
   - Cloudinary
   - YouTube
   - Ghost

## Setup

1. Import the workflow JSON into n8n
2. Configure the required credentials in n8n
3. Set up the PostgreSQL database with the required schema
4. Configure environment variables for API keys
5. Adjust the cron schedule as needed

## File Structure

- `youtube_to_blog_pipeline_with_agents.json` - Main n8n workflow with AI Agents
- `financial-blog-pipeline/` - Python scripts for data models and database connections
  - `shared/` - Shared database models and connections

## Customization

The workflow can be customized for different YouTube channels by modifying the channel ID in the "Set Channel Info" node.

## Monitoring

The workflow logs its execution status to a PostgreSQL database table, allowing for monitoring and troubleshooting.