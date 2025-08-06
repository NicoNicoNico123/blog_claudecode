#!/usr/bin/env python3
"""
Demo script showing the agent-based image generation workflow
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_agent_workflow():
    """Demonstrate the complete agent workflow"""
    print("🤖 Agent-Based Image Generation Demo")
    print("=" * 50)
    
    # Import all agents
    try:
        from image_agents import (
            ImageOrchestratorAgent,
            ImageContextAnalyzerAgent,
            ImagePromptGeneratorAgent,
            ImageGeneratorAgent,
            ImageSearchAgent
        )
        
        # Sample blog content
        sample_content = """
        今天我們來分析台積電的最新財報。作為全球最大的半導體製造商，
        台積電在第二季度實現了15%的營收增長。市場特別關注其3nm製程技術
        的進展，這將直接影響蘋果和高通等主要客戶的訂單。
        
        投資者應該注意以下幾個關鍵點：
        1. 先進製程技術的市場佔有率
        2. 全球晶片短缺對訂單的影響
        3. 與三星在技術上的競爭態勢
        """
        
        sample_title = "台積電Q2財報深度解析"
        
        print("📋 Step 1: Content Analysis")
        print("-" * 30)
        analyzer = ImageContextAnalyzerAgent()
        analysis_result = analyzer.analyze_content(sample_content, sample_title)
        print(f"Strategy: {analysis_result['strategy']}")
        print(f"Contexts found: {len(analysis_result['contexts'])}")
        
        if analysis_result['contexts']:
            for i, context in enumerate(analysis_result['contexts'], 1):
                print(f"  {i}. {context['keyword']} ({context['type']})")
        
        print("\n🔧 Step 2: Prompt Generation")
        print("-" * 30)
        prompter = ImagePromptGeneratorAgent()
        prompts = prompter.generate_prompts(analysis_result['contexts'], sample_content)
        print(f"Prompts generated: {len(prompts)}")
        
        for i, prompt_data in enumerate(prompts, 1):
            print(f"  {i}. {prompt_data['method'].upper()}: {prompt_data['prompt']}")
        
        print("\n⚙️  Step 3: Image Generation/Search")
        print("-" * 30)
        generator = ImageGeneratorAgent()
        searcher = ImageSearchAgent()
        
        generated_images = generator.generate_images(prompts)
        searched_images = searcher.search_images(prompts)
        
        print(f"Generated images: {len(generated_images)}")
        print(f"Searched images: {len(searched_images)}")
        
        print("\n🎨 Step 4: Final Results")
        print("-" * 30)
        orchestrator = ImageOrchestratorAgent()
        final_images = orchestrator.generate_images(sample_content, sample_title)
        print(f"Total images: {len(final_images)}")
        
        if final_images:
            for i, img in enumerate(final_images, 1):
                print(f"  {i}. {img}")
        else:
            print("  No images generated (requires API keys)")
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in demo: {e}")
        print("Make sure you're running this script from the correct directory.")

if __name__ == "__main__":
    demo_agent_workflow()