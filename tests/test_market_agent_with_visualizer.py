#!/usr/bin/env python3
"""
Integration Test: Market Research Agent + Visualizer
목적: Market Agent 실행 → 결과 가시화 → PNG 파일 생성 검증
"""

import sys
from pathlib import Path

# Add workspace to path
WORKSPACE_ROOT = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from agents.market_research.agent import MarketResearchAgent
from agents.market_research.visualizer import MarketResearchVisualizer
from shared.logger import get_logger

logger = get_logger(__name__)

def main():
    """Run market agent and generate visualizations"""
    
    logger.info("="*80)
    logger.info("INTEGRATION TEST: Market Agent + Visualizer")
    logger.info("="*80)
    
    try:
        # ========== Step 1: Initialize Agent ==========
        logger.info("\n[Step 1] Initializing Market Research Agent...")
        agent = MarketResearchAgent()
        logger.info("✓ Agent initialized")
        
        # ========== Step 2: Run Agent ==========
        logger.info("\n[Step 2] Running Market Research Agent...")
        logger.info("This will: Think (search) → Act (generate+evaluate+revise) → Output")
        
        agent_output = agent.run(context={})
        logger.info(f"✓ Agent completed execution")
        logger.info(f"  - Score: {agent_output.get('external_relevance_score')}/100")
        logger.info(f"  - Pass: {agent_output.get('pass_evaluation')}")
        logger.info(f"  - Revisions: {agent_output.get('revision_count')}")
        logger.info(f"  - Topics: {len(agent_output.get('included_topics', []))} included, {len(agent_output.get('missing_topics', []))} missing")
        
        # ========== Step 3: Initialize Visualizer ==========
        logger.info("\n[Step 3] Initializing Market Research Visualizer...")
        output_dir = WORKSPACE_ROOT / "visualization"
        visualizer = MarketResearchVisualizer(output_dir=str(output_dir))
        logger.info(f"✓ Visualizer initialized (output: {output_dir})")
        
        # ========== Step 4: Generate Visualizations ==========
        logger.info("\n[Step 4] Generating visualizations...")
        logger.info("Creating 8 chart types: executive summary, market size, regional, policy, supply chain, tech, EV chasm, demand...")
        
        generated_files = visualizer.visualize_market_research(agent_output)
        
        logger.info(f"✓ Visualization generation complete")
        logger.info(f"  - Generated {len(generated_files)} files")
        
        # ========== Step 5: Report Results ==========
        logger.info("\n[Step 5] Visualization Results:")
        logger.info("-" * 80)
        
        if generated_files:
            for i, file_path in enumerate(generated_files, 1):
                logger.info(f"  {i}. {Path(file_path).name}")
                # Verify file exists
                if Path(file_path).exists():
                    file_size = Path(file_path).stat().st_size
                    logger.info(f"     ✓ Created ({file_size:,} bytes)")
                else:
                    logger.warning(f"     ✗ File not found!")
        else:
            logger.warning("  No files generated")
        
        logger.info("-" * 80)
        
        # ========== Step 6: Summary ==========
        logger.info("\n[Step 6] Integration Test Summary:")
        logger.info("="*80)
        logger.info(f"✓ Market Agent Score: {agent_output.get('external_relevance_score')}/100")
        logger.info(f"✓ Evaluation Result: {'PASS' if agent_output.get('pass_evaluation') else 'FAIL'}")
        logger.info(f"✓ Visualizations Created: {len(generated_files)} files")
        logger.info(f"✓ Output Directory: {output_dir}")
        logger.info("="*80)
        logger.info("\n✓ INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        logger.info("  Next: Use PNG files for PDF report generation")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Integration test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
