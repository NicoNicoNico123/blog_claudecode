#!/usr/bin/env python3
"""
AI Agents for the YouTube to Blog Pipeline
This script demonstrates how the AI agents would work in the n8n workflow.
"""

import os
import json
from typing import Dict, List
import openai
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class YouTubeTranscriptExtractorAgent:
    """Agent responsible for extracting YouTube video transcripts"""
    
    def __init__(self):
        # In a real implementation, we would use the YouTube Transcript API
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def extract_transcript(self, video_id: str) -> Dict:
        """Extract transcript from YouTube video"""
        # This is a placeholder - in reality, we would use the YouTube Transcript API
        # For demonstration, we'll return a sample transcript
        return {
            "video_id": video_id,
            "title": "Sample Financial Video",
            "channel_name": "于庭皓",
            "publish_date": "2025-08-07",
            "transcript_text": "This is a sample transcript about financial markets and investment strategies.",
            "duration_seconds": 1800
        }

class BlogGeneratorAgent:
    """Agent responsible for generating blog posts from transcripts"""
    
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def generate_blog_post(self, transcript: str, title: str) -> str:
        """Generate a blog post from transcript"""
        if not self.anthropic_client:
            return "Error: Anthropic API key not available"
        
        prompt = f"""
        基於以下視頻標題和轉錄內容，創建一篇繁體中文的財經部落格文章：
        
        標題：{title}
        
        轉錄內容：
        {transcript}
        
        請按照以下結構創建文章：
        1. 開場鉤子：吸引讀者的開場白
        2. 市場影響：對台灣/美國市場的影響
        3. 新手解釋：簡化的金融概念解釋
        4. 關鍵要點：投資者的可行見解
        
        請使用繁體中文，並創建SEO優化的內容。
        """
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error generating blog post: {str(e)}"

class ImageContextAnalyzerAgent:
    """Agent responsible for analyzing blog content and extracting image contexts"""
    
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def analyze_content(self, content: str, title: str) -> Dict:
        """Analyze blog content and extract image contexts"""
        if not self.anthropic_client:
            return {"contexts": [], "strategy": "fallback"}
        
        analysis_prompt = f"""
        分析以下財經部落格文章內容，並決定需要哪些圖片來增強文章效果。
        
        文章標題：{title}
        
        文章內容：
        {content}
        
        請分析文章內容並提供：
        1. 文章中提到的具體公司、股票或金融產品
        2. 文章討論的主要市場或指數
        3. 文章的核心主題和情感（樂觀、悲觀、中性等）
        4. 建議的圖片類型（圖表、照片、插圖等）
        5. 具體的圖片搜索關鍵詞（繁體中文）
        6. 圖片在文章中的位置建議
        
        回答格式如下：
        公司與股票：[列出所有提到的公司和股票代碼]
        市場指數：[列出相關市場指數]
        核心主題：[描述文章主要討論的主題]
        情感傾向：[樂觀/悲觀/中性]
        圖片建議：[建議的圖片類型和搜索關鍵詞]
        位置建議：[圖片在文章中的位置]
        """
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            analysis = response.content[0].text
            
            # Parse the analysis into structured data
            contexts = self._parse_analysis(analysis)
            
            return {
                "contexts": contexts,
                "strategy": "llm_guided" if contexts else "fallback"
            }
            
        except Exception as e:
            print(f"Error in content analysis: {e}")
            return {"contexts": [], "strategy": "fallback"}
    
    def _parse_analysis(self, analysis: str) -> List[Dict]:
        """Parse LLM analysis into structured contexts"""
        contexts = []
        lines = analysis.split('\n')
        
        for line in lines:
            if '圖片建議：' in line:
                # Extract keywords and image types
                suggestion = line.split('圖片建議：')[-1]
                # Simple parsing - in practice, you might want more sophisticated parsing
                keywords = [kw.strip() for kw in suggestion.split('、') if kw.strip()]
                
                for keyword in keywords[:2]:  # Limit to 2 contexts
                    contexts.append({
                        "keyword": keyword,
                        "type": self._determine_image_type(keyword),
                        "position": "top"  # Default position
                    })
        
        return contexts
    
    def _determine_image_type(self, keyword: str) -> str:
        """Determine image type based on keyword"""
        financial_terms = ['台股', '美股', '港股', '指數', '圖表', '走勢', 'K線', '股價', '財報']
        
        if any(term in keyword for term in financial_terms):
            return "chart"
        elif any(char.isdigit() for char in keyword):
            return "chart"
        else:
            return "photo"

class ImagePromptGeneratorAgent:
    """Agent responsible for generating image prompts based on contexts"""
    
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def generate_prompts(self, contexts: List[Dict], content: str) -> List[Dict]:
        """Generate image prompts for each context"""
        prompts = []
        
        for context in contexts:
            if context["type"] == "chart":
                prompt = self._generate_chart_prompt(context["keyword"])
            else:
                prompt = self._generate_search_prompt(context["keyword"])
            
            prompts.append({
                "context": context,
                "prompt": prompt,
                "method": "generate" if context["type"] == "chart" else "search"
            })
        
        return prompts
    
    def _generate_chart_prompt(self, keyword: str) -> str:
        """Generate prompt for chart generation"""
        return f"Professional financial chart showing {keyword} performance, clean design, green and red colors, Chinese labels"
    
    def _generate_search_prompt(self, keyword: str) -> str:
        """Generate prompt for image search"""
        return keyword

class ImageGeneratorAgent:
    """Agent responsible for generating images using DALL-E"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def generate_images(self, prompts: List[Dict]) -> List[str]:
        """Generate images using DALL-E"""
        images = []
        
        if not self.openai_client:
            print("OpenAI API key not available for image generation.")
            return images
        
        for prompt_data in prompts:
            if prompt_data["method"] == "generate":
                try:
                    response = self.openai_client.images.generate(
                        model="dall-e-3",
                        prompt=prompt_data["prompt"],
                        size="1024x1024",
                        quality="standard",
                        n=1
                    )
                    images.append(response.data[0].url)
                except Exception as e:
                    print(f"Error generating image: {e}")
        
        return images

class ContentFormatterAgent:
    """Agent responsible for formatting content with images"""
    
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def format_content(self, content: str, image_urls: List[str]) -> str:
        """Format content with image URLs"""
        # In a real implementation, we would create a structured format
        # For now, we'll just return the content with image URLs
        formatted_content = content
        for i, url in enumerate(image_urls):
            formatted_content += f"\n\n![Image {i+1}]({url})\n"
        
        return formatted_content

# Example usage
if __name__ == "__main__":
    # Initialize agents
    extractor = YouTubeTranscriptExtractorAgent()
    blog_generator = BlogGeneratorAgent()
    context_analyzer = ImageContextAnalyzerAgent()
    prompt_generator = ImagePromptGeneratorAgent()
    image_generator = ImageGeneratorAgent()
    content_formatter = ContentFormatterAgent()
    
    # Extract transcript
    transcript_data = extractor.extract_transcript("sample_video_id")
    print("Transcript extracted:", transcript_data["title"])
    
    # Generate blog post
    blog_content = blog_generator.generate_blog_post(
        transcript_data["transcript_text"], 
        transcript_data["title"]
    )
    print("Blog post generated")
    
    # Analyze content for images
    analysis_result = context_analyzer.analyze_content(blog_content, transcript_data["title"])
    print("Content analyzed for images")
    
    # Generate prompts
    if analysis_result["contexts"]:
        prompts = prompt_generator.generate_prompts(analysis_result["contexts"], blog_content)
        print("Image prompts generated")
        
        # Generate images (this would be done by the n8n OpenAI node in the actual workflow)
        # image_urls = image_generator.generate_images(prompts)
        # print("Images generated")
        
        # Format content with images
        # formatted_content = content_formatter.format_content(blog_content, image_urls)
        # print("Content formatted with images")
    else:
        print("No image contexts found")