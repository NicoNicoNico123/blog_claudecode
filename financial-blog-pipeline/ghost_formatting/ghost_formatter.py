"""
Ghost Formatter Module
Converts LLM-generated blog content into Ghost CMS compatible format
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import re
import html

class GhostFormatter:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
    def format_blog_post(self, 
                        title: str,
                        content: str,
                        tags: list = None,
                        authors: list = None,
                        feature_image: str = None,
                        excerpt: str = None,
                        meta_title: str = None,
                        meta_description: str = None) -> Dict[str, Any]:
        """
        Format blog post for Ghost CMS
        
        Args:
            title: Blog post title
            content: Main blog content (markdown format)
            tags: List of tags
            authors: List of author IDs
            feature_image: URL for feature image
            excerpt: Post excerpt
            meta_title: SEO meta title
            meta_description: SEO meta description
            
        Returns:
            Ghost-compatible post object
        """
        
        # Clean and format content
        formatted_content = self._clean_content(content)
        
        # Generate excerpt if not provided
        if not excerpt:
            excerpt = self._generate_excerpt(formatted_content)
            
        # Generate SEO meta if not provided
        if not meta_title:
            meta_title = title[:60]  # Ghost limit
            
        if not meta_description:
            meta_description = excerpt[:150]  # SEO best practice
            
        # Prepare tags
        if not tags:
            tags = self._extract_tags_from_content(formatted_content)
            
        # Create Ghost post object
        ghost_post = {
            "posts": [{
                "title": title,
                "slug": self._generate_slug(title),
                "html": self._markdown_to_html(formatted_content),
                "mobiledoc": self._create_mobiledoc(formatted_content),
                "plaintext": self._html_to_plaintext(self._markdown_to_html(formatted_content)),
                "feature_image": feature_image,
                "featured": False,
                "page": False,
                "status": "draft",  # Default to draft
                "locale": "zh-tw",
                "visibility": "public",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "published_at": None,
                "custom_excerpt": excerpt,
                "codeinjection_head": self._generate_seo_meta(meta_title, meta_description),
                "codeinjection_foot": None,
                "og_image": feature_image,
                "og_title": meta_title,
                "og_description": meta_description,
                "twitter_image": feature_image,
                "twitter_title": meta_title,
                "twitter_description": meta_description,
                "meta_title": meta_title,
                "meta_description": meta_description,
                "email_subject": None,
                "email_only": False,
                "tags": tags,
                "authors": authors or ["1"]  # Default author ID
            }]
        }
        
        return ghost_post
    
    def _clean_content(self, content: str) -> str:
        """Clean and format content"""
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Ensure proper spacing around headers
        content = re.sub(r'(#{1,6})([^\s])', r'\1 \2', content)
        
        # Clean up lists
        content = re.sub(r'^\s*-\s*', '- ', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def _generate_excerpt(self, content: str, max_length: int = 300) -> str:
        """Generate excerpt from content"""
        # Remove markdown formatting
        plain_text = re.sub(r'[#*`>_-]', '', content)
        plain_text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', plain_text)
        
        # Take first sentences up to max_length
        sentences = re.split(r'[.!?]+', plain_text)
        excerpt = ""
        
        for sentence in sentences:
            if len(excerpt) + len(sentence) <= max_length:
                excerpt += sentence.strip() + ". "
            else:
                break
                
        return excerpt.strip()
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _extract_tags_from_content(self, content: str) -> list:
        """Extract relevant tags from content"""
        financial_keywords = [
            "股票", "投資", "理財", "基金", "債券", "ETF", "股市", "財經",
            "金融", "經濟", "市場", "分析", "策略", "風險", "回報", "股息"
        ]
        
        tags = []
        for keyword in financial_keywords:
            if keyword in content:
                tags.append({"name": keyword, "slug": keyword.lower()})
                
        return tags[:5]  # Limit to 5 tags max
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML"""
        # Basic markdown conversion
        html_content = markdown
        
        # Headers
        html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        
        # Bold and italic
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)
        
        # Links
        html_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html_content)
        
        # Paragraphs
        paragraphs = html_content.split('\n\n')
        html_content = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
        
        return html_content
    
    def _create_mobiledoc(self, content: str) -> str:
        """Create Ghost mobiledoc format"""
        # Simple mobiledoc structure
        mobiledoc = {
            "version": "0.3.1",
            "markups": [],
            "atoms": [],
            "cards": [],
            "sections": [[1, "p", [[0, [], 0, content[:1000]]]]]
        }
        return json.dumps(mobiledoc)
    
    def _html_to_plaintext(self, html: str) -> str:
        """Convert HTML to plain text"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        return text.strip()
    
    def _generate_seo_meta(self, title: str, description: str) -> str:
        """Generate SEO meta tags"""
        return f'''
<meta name="title" content="{html.escape(title)}">
<meta name="description" content="{html.escape(description)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(description)}">
'''
    
    def save_formatted_post(self, ghost_post: Dict[str, Any], filename: str = None) -> str:
        """Save formatted post to file"""
        if not filename:
            filename = f"ghost_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        output_path = os.path.join(os.path.dirname(__file__), 'outputs', filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ghost_post, f, ensure_ascii=False, indent=2)
            
        return output_path
    
    def load_blog_draft(self, draft_path: str) -> Dict[str, Any]:
        """Load LLM-generated blog draft"""
        with open(draft_path, 'r', encoding='utf-8') as f:
            return json.load(f)


if __name__ == "__main__":
    # Test the formatter
    formatter = GhostFormatter()
    
    test_content = """# 股市分析：今日市場回顧

## 市場概況
今日台灣加權指數上漲100點，成交量達到2000億元。

主要上漲的類股包括科技股和金融股，其中**台積電**表現最為突出。

### 投資建議
- 關注科技股
- 留意風險管理
- 長期投資策略"""
    
    ghost_post = formatter.format_blog_post(
        title="股市分析：今日市場回顧",
        content=test_content,
        tags=[{"name": "股市分析", "slug": "stock-analysis"}],
        feature_image="https://example.com/stock-image.jpg"
    )
    
    output_file = formatter.save_formatted_post(ghost_post, "test_ghost_post.json")
    print(f"Formatted post saved to: {output_file}")