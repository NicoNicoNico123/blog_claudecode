"""
Ghost Uploader Module
Handles uploading formatted blog posts to Ghost CMS
"""

import json
import os
import requests
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GhostUploader:
    def __init__(self, ghost_url: str = None, admin_api_key: str = None):
        self.ghost_url = ghost_url or os.getenv('GHOST_URL')
        self.admin_api_key = admin_api_key or os.getenv('GHOST_ADMIN_API_KEY')
        
        if not self.ghost_url or not self.admin_api_key:
            raise ValueError("Ghost URL and Admin API Key are required")
            
        self.session = requests.Session()
        self._setup_headers()
        
    def _setup_headers(self):
        """Setup authentication headers for Ghost Admin API"""
        import jwt
        import time
        
        # Split the admin API key
        key_parts = self.admin_api_key.split(':')
        if len(key_parts) != 2:
            raise ValueError("Invalid Ghost Admin API Key format")
            
        id, secret = key_parts
        
        # Generate JWT token
        now = int(time.time())
        payload = {
            'iat': now,
            'exp': now + 5 * 60,  # 5 minutes
            'aud': '/admin/'
        }
        
        token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256')
        
        self.session.headers.update({
            'Authorization': f'Ghost {token}',
            'Content-Type': 'application/json',
            'Accept-Version': 'v5.0'
        })
    
    def create_post(self, ghost_post: Dict[str, Any], publish: bool = False) -> Dict[str, Any]:
        """
        Create a new post in Ghost CMS
        
        Args:
            ghost_post: Formatted Ghost post object
            publish: Whether to publish immediately or save as draft
            
        Returns:
            Response from Ghost API
        """
        
        # Update status if publishing
        if publish:
            ghost_post['posts'][0]['status'] = 'published'
            ghost_post['posts'][0]['published_at'] = datetime.utcnow().isoformat() + "Z"
            
        try:
            response = self.session.post(
                f"{self.ghost_url}/ghost/api/admin/posts/",
                json=ghost_post
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Post created successfully: {result['posts'][0]['title']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create post: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def update_post(self, post_id: str, ghost_post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing post in Ghost CMS
        
        Args:
            post_id: ID of the post to update
            ghost_post: Updated Ghost post object
            
        Returns:
            Response from Ghost API
        """
        
        try:
            response = self.session.put(
                f"{self.ghost_url}/ghost/api/admin/posts/{post_id}/",
                json=ghost_post
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Post updated successfully: {result['posts'][0]['title']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update post: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def upload_feature_image(self, image_path: str, image_name: str = None) -> Optional[str]:
        """
        Upload feature image to Ghost
        
        Args:
            image_path: Path to the image file
            image_name: Optional name for the image
            
        Returns:
            Image URL if successful, None otherwise
        """
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
            
        if not image_name:
            image_name = os.path.basename(image_path)
            
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_name, f, 'image/jpeg')}
                response = self.session.post(
                    f"{self.ghost_url}/ghost/api/admin/images/upload/",
                    files=files
                )
                response.raise_for_status()
                
                result = response.json()
                image_url = result['images'][0]['url']
                logger.info(f"Image uploaded successfully: {image_url}")
                return image_url
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload image: {e}")
            return None
    
    def get_tags(self) -> Dict[str, Any]:
        """Get all existing tags from Ghost"""
        try:
            response = self.session.get(f"{self.ghost_url}/ghost/api/admin/tags/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get tags: {e}")
            return {"tags": []}
    
    def create_tag(self, tag_name: str, tag_slug: str = None) -> Dict[str, Any]:
        """Create a new tag in Ghost"""
        if not tag_slug:
            tag_slug = tag_name.lower().replace(' ', '-')
            
        tag_data = {
            "tags": [{
                "name": tag_name,
                "slug": tag_slug
            }]
        }
        
        try:
            response = self.session.post(
                f"{self.ghost_url}/ghost/api/admin/tags/",
                json=tag_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create tag: {e}")
            raise
    
    def get_posts(self, limit: int = 15, page: int = 1) -> Dict[str, Any]:
        """Get existing posts from Ghost"""
        try:
            params = {
                'limit': limit,
                'page': page,
                'order': 'created_at DESC'
            }
            response = self.session.get(
                f"{self.ghost_url}/ghost/api/admin/posts/",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get posts: {e}")
            return {"posts": []}
    
    def delete_post(self, post_id: str) -> bool:
        """Delete a post from Ghost"""
        try:
            response = self.session.delete(
                f"{self.ghost_url}/ghost/api/admin/posts/{post_id}/"
            )
            response.raise_for_status()
            logger.info(f"Post deleted successfully: {post_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete post: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to Ghost CMS"""
        try:
            response = self.session.get(f"{self.ghost_url}/ghost/api/admin/site/")
            response.raise_for_status()
            site_info = response.json()
            logger.info(f"Connected to Ghost: {site_info.get('sites', [{}])[0].get('title', 'Unknown')}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ghost: {e}")
            return False
    
    def save_upload_log(self, post_data: Dict[str, Any], filename: str = None) -> str:
        """Save upload log for tracking"""
        if not filename:
            filename = f"upload_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        output_path = os.path.join(os.path.dirname(__file__), 'outputs', filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        log_data = {
            "uploaded_at": datetime.utcnow().isoformat(),
            "ghost_response": post_data,
            "post_url": f"{self.ghost_url}/{post_data['posts'][0]['slug']}" if post_data.get('posts') else None
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
            
        return output_path


if __name__ == "__main__":
    # Test connection
    try:
        uploader = GhostUploader()
        
        if uploader.test_connection():
            print("✅ Successfully connected to Ghost CMS")
            
            # Get existing posts
            posts = uploader.get_posts(limit=5)
            print(f"📊 Found {len(posts.get('posts', []))} existing posts")
            
            # Get existing tags
            tags = uploader.get_tags()
            print(f"🏷️  Found {len(tags.get('tags', []))} existing tags")
            
        else:
            print("❌ Failed to connect to Ghost CMS")
            
    except Exception as e:
        print(f"❌ Error: {e}")