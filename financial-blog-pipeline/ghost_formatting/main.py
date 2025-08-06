#!/usr/bin/env python3
"""
Phase 3: Ghost Blog Formatting and Uploading
Main orchestration script for formatting LLM-generated blog posts and uploading to Ghost CMS
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ghost_formatter import GhostFormatter
from ghost_uploader import GhostUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/phase3.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Phase3Orchestrator:
    def __init__(self):
        self.formatter = GhostFormatter()
        self.uploader = None
        
    def initialize_uploader(self):
        """Initialize Ghost uploader with environment variables"""
        try:
            self.uploader = GhostUploader()
            logger.info("Ghost uploader initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Ghost uploader: {e}")
            return False
    
    def process_single_blog(self, draft_path: str, publish: bool = False) -> Dict[str, Any]:
        """
        Process a single blog draft
        
        Args:
            draft_path: Path to the LLM-generated blog draft
            publish: Whether to publish immediately or save as draft
            
        Returns:
            Processing result with status and details
        """
        
        logger.info(f"Processing blog draft: {draft_path}")
        
        try:
            # Load the blog draft
            with open(draft_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            # Extract content
            title = draft_data.get('title', '')
            content = draft_data.get('content', '')
            tags = draft_data.get('tags', [])
            feature_image = draft_data.get('feature_image', '')
            excerpt = draft_data.get('excerpt', '')
            
            # Format for Ghost
            ghost_post = self.formatter.format_blog_post(
                title=title,
                content=content,
                tags=tags,
                feature_image=feature_image,
                excerpt=excerpt
            )
            
            # Save formatted post
            formatted_path = self.formatter.save_formatted_post(
                ghost_post, 
                f"formatted_{Path(draft_path).stem}.json"
            )
            
            # Upload to Ghost if uploader is available
            upload_result = None
            if self.uploader and self.uploader.test_connection():
                upload_result = self.uploader.create_post(ghost_post, publish=publish)
                
                # Save upload log
                log_path = self.uploader.save_upload_log(upload_result)
                
                logger.info(f"Blog uploaded successfully: {upload_result['posts'][0]['title']}")
                logger.info(f"Post URL: {upload_result['posts'][0]['url']}")
            else:
                logger.warning("Ghost uploader not available, skipping upload")
            
            return {
                "status": "success",
                "draft_path": draft_path,
                "formatted_path": formatted_path,
                "upload_result": upload_result,
                "title": title
            }
            
        except Exception as e:
            logger.error(f"Error processing blog draft {draft_path}: {e}")
            return {
                "status": "error",
                "draft_path": draft_path,
                "error": str(e)
            }
    
    def process_batch(self, drafts_dir: str, publish: bool = False) -> Dict[str, Any]:
        """
        Process multiple blog drafts in batch
        
        Args:
            drafts_dir: Directory containing blog drafts
            publish: Whether to publish immediately or save as drafts
            
        Returns:
            Batch processing results
        """
        
        logger.info(f"Processing batch of blog drafts from: {drafts_dir}")
        
        results = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        # Find all JSON files in the directory
        draft_files = [f for f in Path(drafts_dir).glob('*.json') 
                      if not f.name.startswith('formatted_')]
        
        if not draft_files:
            logger.warning(f"No blog drafts found in {drafts_dir}")
            return results
        
        results["total_processed"] = len(draft_files)
        
        for draft_file in draft_files:
            logger.info(f"Processing: {draft_file.name}")
            
            result = self.process_single_blog(str(draft_file), publish=publish)
            results["details"].append(result)
            
            if result["status"] == "success":
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"Batch processing complete: {results['successful']}/{results['total_processed']} successful")
        
        # Save batch results
        batch_result_path = os.path.join(
            os.path.dirname(__file__), 
            'outputs', 
            f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(batch_result_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return results
    
    def validate_environment(self) -> Dict[str, bool]:
        """Validate that all required environment variables are set"""
        
        required_vars = [
            'GHOST_URL',
            'GHOST_ADMIN_API_KEY'
        ]
        
        validation_results = {}
        
        for var in required_vars:
            value = os.getenv(var)
            validation_results[var] = bool(value)
            if not value:
                logger.error(f"Missing required environment variable: {var}")
        
        return validation_results
    
    def get_processing_summary(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable summary of processing results"""
        
        summary = f"""
=== Phase 3 Processing Summary ===
Total drafts processed: {results.get('total_processed', 0)}
Successfully formatted: {results.get('successful', 0)}
Failed: {results.get('failed', 0)}

"""
        
        if results.get('details'):
            summary += "Individual results:\n"
            for detail in results['details']:
                status = "✅" if detail['status'] == 'success' else "❌"
                summary += f"{status} {detail.get('title', 'Unknown')} - {detail['status']}\n"
        
        return summary


def main():
    parser = argparse.ArgumentParser(description="Phase 3: Ghost Blog Formatting and Uploading")
    parser.add_argument('--single', type=str, help='Path to single blog draft')
    parser.add_argument('--batch', type=str, help='Directory containing blog drafts')
    parser.add_argument('--publish', action='store_true', help='Publish immediately instead of saving as draft')
    parser.add_argument('--validate', action='store_true', help='Validate environment setup')
    parser.add_argument('--test-connection', action='store_true', help='Test Ghost CMS connection')
    
    args = parser.parse_args()
    
    orchestrator = Phase3Orchestrator()
    
    # Validate environment
    validation = orchestrator.validate_environment()
    
    if args.validate:
        print("Environment validation:")
        for var, valid in validation.items():
            status = "✅" if valid else "❌"
            print(f"{status} {var}")
        return
    
    # Initialize uploader if environment is valid
    if all(validation.values()):
        orchestrator.initialize_uploader()
    
    if args.test_connection:
        if orchestrator.uploader:
            success = orchestrator.uploader.test_connection()
            if success:
                print("✅ Successfully connected to Ghost CMS")
            else:
                print("❌ Failed to connect to Ghost CMS")
        else:
            print("❌ Cannot test connection - uploader not initialized")
        return
    
    # Process single file
    if args.single:
        result = orchestrator.process_single_blog(args.single, publish=args.publish)
        print(orchestrator.get_processing_summary({"details": [result]}))
        
    # Process batch
    elif args.batch:
        results = orchestrator.process_batch(args.batch, publish=args.publish)
        print(orchestrator.get_processing_summary(results))
        
    else:
        # Default: process all drafts in standard output directory
        default_drafts_dir = "../phase4_generation/outputs/blog_drafts"
        if os.path.exists(default_drafts_dir):
            results = orchestrator.process_batch(default_drafts_dir, publish=args.publish)
            print(orchestrator.get_processing_summary(results))
        else:
            print("No blog drafts found. Use --single or --batch to specify files.")


if __name__ == "__main__":
    main()