#!/usr/bin/env python3
"""
Test script to demonstrate the agent-based image generation functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_agent_based_image_generation():
    """Test the agent-based image generation functionality"""
    print("🔍 Testing agent-based image generation functionality...")
    
    # Import the image orchestrator agent directly
    try:
        from image_agents import ImageOrchestratorAgent
        
        # Create orchestrator
        orchestrator = ImageOrchestratorAgent()
        
        # Sample blog content for testing
        sample_content = """
        今天我們來談談台積電的最新動態。台積電作為全球最大的半導體製造商，
        最近公布了第二季度的財報，顯示營收成長了15%。這對台灣股市來說是一個
        重要的信號，特別是對於科技股板塊。
        
        投資者應該關注台積電的5nm和3nm製程技術，這些先進技術是公司競爭優勢
        的關鍵。同時，我們也要注意全球晶片短缺問題對整個行業的影響。
        """
        
        sample_title = "台積電財報分析：科技股的領頭羊"
        
        # Test the image generation process
        print("\n📝 Analyzing blog content for image generation...")
        images = orchestrator.generate_images(sample_content, sample_title)
        
        if images:
            print(f"\n🖼️  Generated images:")
            for i, img in enumerate(images, 1):
                print(f"  {i}. {img}")
        else:
            print("\nℹ️  No images generated (expected without API keys)")
            print("   In a real implementation with API keys, this would generate or search for images.")
            
    except Exception as e:
        print(f"❌ Error testing agent-based image generation: {e}")
        print("   Make sure you're running this script from the correct directory.")

def test_direct_agents():
    """Test individual agents directly"""
    print("\n🔧 Testing individual agents...")
    
    try:
        from image_agents import (
            ImageContextAnalyzerAgent,
            ImagePromptGeneratorAgent,
            ImageGeneratorAgent,
            ImageSearchAgent
        )
        
        # Test context analyzer
        print("  📊 Testing context analyzer...")
        analyzer = ImageContextAnalyzerAgent()
        
        sample_content = "台積電股價近期表現強勁，市場關注其先進製程技術進展。"
        sample_title = "台積電技術分析"
        
        result = analyzer.analyze_content(sample_content, sample_title)
        print(f"    Analysis result: {result['strategy']}")
        
        print("  ✅ Individual agent tests completed.")
        
    except Exception as e:
        print(f"  ❌ Error testing individual agents: {e}")

if __name__ == "__main__":
    test_agent_based_image_generation()
    test_direct_agents()