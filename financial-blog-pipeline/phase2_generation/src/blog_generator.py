#!/usr/bin/env python3
"""
Enhanced blog generator with Cantonese financial blogger support and image enrichment
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psycopg2
from dotenv import load_dotenv
import openai
import anthropic
from PIL import Image
import io
import base64

load_dotenv()

class FinancialBlogGenerator:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.db_connection = self._get_database_connection()
        
    def _get_database_connection(self):
        """Get PostgreSQL connection"""
        host = os.getenv('POSTGRES_HOST')
        port = os.getenv('POSTGRES_PORT')
        database = os.getenv('POSTGRES_DATABASE')
        user = os.getenv('POSTGRES_USER', 'root')
        password = os.getenv('POSTGRES_PASSWORD')
        
        conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return psycopg2.connect(conn_string)
    
    def get_latest_transcript(self, channel_name: str = "于庭皓", limit: int = 1) -> List[Dict]:
        """Get latest transcript from database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT video_id, title, channel_name, publish_date, transcript_text, duration_seconds
                FROM video_transcripts 
                WHERE channel_name = %s
                ORDER BY publish_date DESC
                LIMIT %s
            """, (channel_name, limit))
            
            columns = ['video_id', 'title', 'channel_name', 'publish_date', 'transcript_text', 'duration_seconds']
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            print(f"❌ Error getting transcript: {e}")
            return []
    
    def generate_traditional_chinese_blog(self, transcript: str, title: str) -> Dict:
        """Generate Traditional Chinese financial blog"""
        prompt = f"""
        你是一位專業的財經部落客，請根據以下影片逐字稿，撰寫一篇引人入勝的財經部落格文章。
        
        原始標題：{title}
        
        逐字稿內容：
        {transcript[:5000]}...
        
        請按照以下結構撰寫：
        
        1. **開場吸睛** (Hook) - 用有趣的開場吸引讀者
        2. **市場影響分析** - 說明這對投資者的實際影響
        3. **小白也能懂** - 用簡單語言解釋複雜概念
        4. **關鍵結論** - 提供3-5個具體投資建議
        
        要求：
        - 使用繁體中文
        - 加入相關股票代碼
        - 提供具體數字和時間點
        - 字數約800-1200字
        - SEO優化的標題和副標題
        """
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return {
                "language": "traditional_chinese",
                "title": f"【財經分析】{title}",
                "content": content,
                "tags": ["財經", "投資", "市場分析", "台灣股市"],
                "meta_description": f"深入分析{title}對投資市場的影響"
            }
            
        except Exception as e:
            print(f"❌ Error generating Traditional Chinese blog: {e}")
            return None
    
    def generate_cantonese_blog(self, transcript: str, title: str) -> Dict:
        """Generate Cantonese financial blog with authentic tone"""
        prompt = f"""
        你是一位地道嘅香港財經KOL，用廣東話同香港人講財經。
        
        影片標題：{title}
        
        逐字稿：
        {transcript[:5000]}...
        
        請用以下風格寫一篇廣東話財經文：
        
        1. **開場白** - 用「大家好，我係...」開始
        2. **市場分析** - 用香港人熟悉嘅例子
        3. **投資貼士** - 「記住呢幾點」
        4. **結語** - 地道嘅鼓勵說話
        
        要求：
        - 純正廣東話（唔好簡體字）
        - 加入香港股票代號
        - 用「你哋」而唔係「你們」
        - 加入「其實」、「不過」、「咁樣」等廣東話詞語
        - 字數約600-800字
        """
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return {
                "language": "cantonese",
                "title": f"【財經拆解】{title}",
                "content": content,
                "tags": ["財經", "投資", "港股", "廣東話"],
                "meta_description": f"用廣東話同你講{title}嘅投資啟示"
            }
            
        except Exception as e:
            print(f"❌ Error generating Cantonese blog: {e}")
            return None
    
    def generate_images(self, content: str, title: str) -> List[str]:
        """Generate relevant images for blog content"""
        images = []
        
        # Search for stock-related keywords
        keywords = [
            "台積電", "台股", "美股", "港股", "恒生指數", "科技股",
            "金融股", "房地產", "加密貨幣", "AI", "半導體"
        ]
        
        # Generate stock chart image
        stock_keywords = [k for k in keywords if k in content]
        if stock_keywords:
            images.append(self._generate_stock_chart(stock_keywords[0]))
        
        # Generate market sentiment image
        images.append(self._generate_market_sentiment(content))
        
        return [img for img in images if img]
    
    def _generate_stock_chart(self, keyword: str) -> str:
        """Generate stock chart image"""
        prompt = f"Professional stock chart showing {keyword} performance, clean financial design, green and red colors, Chinese labels"
        
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            return response.data[0].url
        except Exception as e:
            print(f"❌ Error generating stock chart: {e}")
            return None
    
    def _generate_market_sentiment(self, content: str) -> str:
        """Generate market sentiment visualization"""
        prompt = "Modern financial market sentiment visualization, bullish/bearish indicators, clean infographic style, Chinese financial theme"
        
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            return response.data[0].url
        except Exception as e:
            print(f"❌ Error generating sentiment image: {e}")
            return None
    
    def extract_images_from_content(self, content: str) -> List[str]:
        """Extract relevant stock images or charts mentioned in content"""
        # This would integrate with stock image APIs
        # For now, placeholder for future implementation
        return []
    
    def create_ghost_post(self, blog_data: Dict, images: List[str]) -> Dict:
        """Format blog post for Ghost CMS"""
        image_html = ""
        for i, img_url in enumerate(images):
            image_html += f'<img src="{img_url}" alt="{blog_data["title"]} image {i+1}" class="post-image" />\n'
        
        content_with_images = f"""
        {image_html}
        
        {blog_data["content"]}
        
        <div class="post-footer">
            <p><em>本文內容僅供參考，投資有風險，請謹慎評估。</em></p>
        </div>
        """
        
        return {
            "title": blog_data["title"],
            "html": content_with_images,
            "tags": blog_data["tags"],
            "meta_description": blog_data["meta_description"],
            "published_at": datetime.now().isoformat(),
            "featured": False,
            "visibility": "public"
        }
    
    def generate_comprehensive_blog(self, video_data: Dict, include_cantonese: bool = True) -> Dict:
        """Generate both Traditional Chinese and Cantonese blogs with images"""
        
        # Generate Traditional Chinese blog
        tc_blog = self.generate_traditional_chinese_blog(
            video_data["transcript_text"], 
            video_data["title"]
        )
        
        # Generate Cantonese blog if requested
        cantonese_blog = None
        if include_cantonese:
            cantonese_blog = self.generate_cantonese_blog(
                video_data["transcript_text"], 
                video_data["title"]
            )
        
        # Generate images
        images = self.generate_images(video_data["transcript_text"], video_data["title"])
        
        # Create Ghost posts
        posts = []
        
        if tc_blog:
            posts.append({
                "language": "traditional_chinese",
                "post": self.create_ghost_post(tc_blog, images)
            })
        
        if cantonese_blog:
            posts.append({
                "language": "cantonese", 
                "post": self.create_ghost_post(cantonese_blog, images)
            })
        
        return {
            "original_video": video_data,
            "generated_posts": posts,
            "images": images
        }

def main():
    """Main entry point for Phase 2"""
    generator = FinancialBlogGenerator()
    
    # Get latest transcript
    transcripts = generator.get_latest_transcript(channel_name="于庭皓", limit=1)
    
    if not transcripts:
        print("❌ No transcripts found")
        return
    
    video_data = transcripts[0]
    print(f"🎯 Processing: {video_data['title']}")
    
    # Generate comprehensive blog
    result = generator.generate_comprehensive_blog(video_data, include_cantonese=True)
    
    # Save results
    output_dir = "/Users/nico/coding/blog_claudecode/financial-blog-pipeline/phase2_generation/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{video_data['video_id']}_blogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ Generated {len(result['generated_posts'])} blog posts")
    print(f"📁 Saved to: {filepath}")
    
    # Preview first blog
    for post_data in result['generated_posts']:
        lang = post_data['language']
        title = post_data['post']['title']
        print(f"\n📝 {lang.upper()} Blog: {title}")
        print(f"   Tags: {', '.join(post_data['post']['tags'])}")
        print(f"   Images: {len(result['images'])}")

if __name__ == "__main__":
    main()