#!/usr/bin/env python3
"""
Specialized agents for image generation workflow
"""

import os
import json
import requests
from typing import Dict, List, Optional
import openai
import anthropic
from dotenv import load_dotenv

load_dotenv()

class ImageContextAnalyzerAgent:
    """Agent responsible for analyzing blog content and extracting image contexts"""
    
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY')) if os.getenv('ANTHROPIC_API_KEY') else None
    
    def analyze_content(self, content: str, title: str) -> Dict:
        """Analyze blog content and extract image contexts"""
        if not self.anthropic_client:
            print("❌ Anthropic API key not available for context analysis.")
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
            print(f"❌ Error in content analysis: {e}")
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
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY')) if os.getenv('ANTHROPIC_API_KEY') else None
    
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
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
    
    def generate_images(self, prompts: List[Dict]) -> List[str]:
        """Generate images using DALL-E"""
        images = []
        
        if not self.openai_client:
            print("❌ OpenAI API key not available for image generation.")
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
                    print(f"❌ Error generating image: {e}")
        
        return images

class ImageSearchAgent:
    """Agent responsible for searching images using Unsplash"""
    
    def __init__(self):
        self.unsplash_api_key = os.getenv('UNSPLASH_API_KEY')
    
    def search_images(self, prompts: List[Dict]) -> List[str]:
        """Search images using Unsplash"""
        images = []
        
        if not self.unsplash_api_key:
            print("❌ Unsplash API key not available for image search.")
            return images
        
        for prompt_data in prompts:
            if prompt_data["method"] == "search":
                try:
                    url = "https://api.unsplash.com/search/photos"
                    headers = {"Authorization": f"Client-ID {self.unsplash_api_key}"}
                    params = {
                        "query": prompt_data["prompt"],
                        "per_page": 1,
                        "orientation": "landscape"
                    }
                    
                    response = requests.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    if data["results"]:
                        images.append(data["results"][0]["urls"]["regular"])
                except Exception as e:
                    print(f"❌ Error searching for image: {e}")
        
        return images

class ImageOrchestratorAgent:
    """Orchestrator agent that coordinates all image generation tasks"""
    
    def __init__(self):
        self.context_analyzer = ImageContextAnalyzerAgent()
        self.prompt_generator = ImagePromptGeneratorAgent()
        self.image_generator = ImageGeneratorAgent()
        self.image_searcher = ImageSearchAgent()
    
    def generate_images(self, content: str, title: str) -> List[str]:
        """Main method to orchestrate image generation workflow"""
        # Step 1: Analyze content to extract contexts
        print("🔍 Analyzing blog content for image contexts...")
        analysis_result = self.context_analyzer.analyze_content(content, title)
        
        if not analysis_result["contexts"]:
            print("ℹ️  No image contexts found, using fallback method.")
            return self._fallback_generation(content)
        
        # Step 2: Generate prompts based on contexts
        print("📝 Generating image prompts...")
        prompts = self.prompt_generator.generate_prompts(analysis_result["contexts"], content)
        
        # Step 3: Generate images using appropriate methods
        print("🖼️  Generating/searching images...")
        generated_images = self.image_generator.generate_images(prompts)
        searched_images = self.image_searcher.search_images(prompts)
        
        # Combine all images
        all_images = generated_images + searched_images
        
        print(f"✅ Generated {len(all_images)} images")
        return [img for img in all_images if img]
    
    def _fallback_generation(self, content: str) -> List[str]:
        """Fallback method when LLM analysis fails"""
        # Simple keyword-based approach
        keywords = [
            "台積電", "台股", "美股", "港股", "恒生指數", "科技股",
            "金融股", "房地產", "加密貨幣", "AI", "半導體"
        ]
        
        found_keywords = [k for k in keywords if k in content]
        images = []
        
        if found_keywords and isinstance(self.image_generator, ImageGeneratorAgent) and self.image_generator.openai_client:
            try:
                response = self.image_generator.openai_client.images.generate(
                    model="dall-e-3",
                    prompt=f"Professional financial chart showing {found_keywords[0]} performance",
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                images.append(response.data[0].url)
            except Exception as e:
                print(f"❌ Error in fallback generation: {e}")
        
        return images