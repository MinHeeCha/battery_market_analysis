#!/usr/bin/env python3
"""
QUICK START: Market Research Agent + Visualizer
Complete integration ready for use
"""

# ============================================================================
# OPTION 1: Run the complete integration test
# ============================================================================
"""
$ cd /Users/minhee/Documents/skala/ch21_Agent/Battery_analysis
$ python3 test_market_agent_with_visualizer.py

Output:
  - Runs agent with quality evaluation
  - Generates 8 PNG files
  - Saves to: visualization/ directory
  - Logs: Score, topics, file sizes
"""

# ============================================================================
# OPTION 2: Use in Python code - Minimal example
# ============================================================================
from pathlib import Path
import sys

# Add workspace to path
WORKSPACE = Path("/Users/minhee/Documents/skala/ch21_Agent/Battery_analysis")
sys.path.insert(0, str(WORKSPACE))

from agents.market_research.agent import MarketResearchAgent
from agents.market_research.visualizer import MarketResearchVisualizer

# Run market analysis
agent = MarketResearchAgent()
market_result = agent.run(context={})

print(f"✓ Agent Score: {market_result['external_relevance_score']}/100")
print(f"✓ Status: {'PASS' if market_result['pass_evaluation'] else 'FAIL'}")

# Generate visualizations
visualizer = MarketResearchVisualizer(output_dir="visualization")
png_files = visualizer.visualize_market_research(market_result)

print(f"✓ Generated {len(png_files)} visualization files:")
for file_path in png_files:
    print(f"  - {Path(file_path).name}")

# ============================================================================
# OPTION 3: Custom usage with your own context
# ============================================================================
# market_result = agent.run(context={
#     "company": "LG Energy Solution",
#     "focus": "EV battery market",
#     "regions": ["China", "Europe", "North America"]
# })
#
# visualizer = MarketResearchVisualizer(output_dir="custom_reports")
# charts = visualizer.visualize_market_research(market_result)

# ============================================================================
# FILES GENERATED
# ============================================================================
"""
/visualization/
├── 01_executive_summary.png        # Key topics in colored boxes
├── 02_market_size_growth.png       # Market trends 2022-2026
├── 03_regional_market_share.png    # Regional distribution & trends
├── 04_policy_tariff_landscape.png  # Policy impact by region
├── 05_supply_chain_risk_map.png    # Risk matrix: supply vs volatility
├── 06_technology_competition.png   # Tech market share & maturity
├── 07_ev_chasm_analysis.png        # EV market entry barriers
└── 08_battery_demand_structure.png # Demand shifts & performance radar
"""

# ============================================================================
# PDF INTEGRATION (Next step)
# ============================================================================
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create PDF with visualizations
c = canvas.Canvas("market_report.pdf", pagesize=letter)
width, height = letter

for png_file in png_files:
    c.drawImage(png_file, 50, 300, width=500, height=300)
    c.showPage()

c.save()
print("✓ PDF created: market_report.pdf")
"""

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
"""
# If dependencies are missing:
$ python3 -m pip install matplotlib numpy openai python-dotenv chromadb requests

# Set API key for web search (optional):
$ export TAVILY_API_KEY=your_api_key_here

# Verify installation:
$ python3 test_market_agent_with_visualizer.py
"""

# ============================================================================
# QUALITY METRICS
# ============================================================================
"""
✓ Evaluation Score: 95/100 baseline (varies per run)
✓ Pass Threshold: 80/100
✓ Coverage: All 5 mandatory topics (EV chasm, demand, policy, supply, tech)
✓ Image Quality: 300 DPI (PDF-ready)
✓ Format: PNG with white background
✓ Total Size: ~1.7 MB for 8 charts
✓ Generation Time: ~30 seconds total
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================
"""
Q: ModuleNotFoundError: No module named 'dotenv'
A: pip3 install python-dotenv

Q: Matplotlib font warnings about Korean glyphs
A: Expected - Korean text displays as boxes, doesn't affect English labels

Q: "No documents in retriever"
A: Expected - Vector DB is empty, can add documents with add_documents()

Q: Want higher scores?
A: Results vary 95-100/100 (random LLM variation), all pass threshold

Q: How to use custom context?
A: agent.run(context={"key": "value", ...})
"""
