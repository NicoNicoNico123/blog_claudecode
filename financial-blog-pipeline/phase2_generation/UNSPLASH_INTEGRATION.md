# Image Search Integration

This project uses the Unsplash API for searching relevant images for blog posts.

## Setup

1. Visit [Unsplash Developers](https://unsplash.com/developers) and create an account
2. Create a new application to get your API key
3. Add your API key to the `.env` file:

```
UNSPLASH_API_KEY=your_actual_unsplash_api_key_here
```

## Usage

The image search functionality is automatically used when:
1. The blog content is analyzed by the LLM
2. The system determines that existing images would be more appropriate than generated ones
3. Keywords are extracted from the blog content for searching

## How it works

1. The LLM analyzes the blog content to identify relevant keywords
2. For each keyword, the system decides whether to:
   - Generate a new image (for charts, diagrams, etc.)
   - Search for existing images (for photos, illustrations, etc.)
3. When searching, the Unsplash API is called with the keyword
4. The most relevant image is selected and added to the blog post

## Rate Limits

Unsplash has rate limits for their API:
- 50 requests per hour for development keys
- 5000 requests per hour for production keys

Make sure to handle rate limiting appropriately in your application.