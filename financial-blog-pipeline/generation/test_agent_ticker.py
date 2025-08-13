#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from generation_pipeline.finalize import enrich_tickers_with_agent

# Test HTML content similar to what we're seeing
test_html = """<h2>2025/8/11 全美投資潮 牛市剛起跑？</h2>

<h3>川普關稅策略與半導體業豁免</h3>

<p>蘋果因追加1,000億美元的國內製造業投資，讓市場預期從印度和中國輸出到美國的iPhone可免關稅，引得市場進入全面性樂觀。</p>

<p>輝達和超微已經同意將在中國銷售的特別晶片所得營收的55%交給美國政府，作為核發出口許可的交換條件。</p>

<p>台積電、三星、博通、蘋果等企業只要願意在美國擴大投資，就有機會持續性豁免關稅。</p>"""

print("Original HTML:")
print(test_html)
print("\n" + "="*50 + "\n")

# You'll need to set your OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("❌ OPENAI_API_KEY environment variable not set")
    print("Please set it to test the agent-based ticker enrichment")
    sys.exit(1)

result = enrich_tickers_with_agent(
    test_html,
    openai_api_key=openai_api_key,
    openai_model="gpt-4o-mini"
)

print("After agent-based ticker enrichment:")
print(result)
print("\n" + "="*50 + "\n")

# Check for specific companies
companies = ["蘋果", "輝達", "超微", "台積電"]
for company in companies:
    if f"{company}(" in result:
        print(f"✅ {company} was enriched with ticker")
    elif company in result:
        print(f"❌ {company} found but NOT enriched")
    else:
        print(f"❓ {company} not found in content")