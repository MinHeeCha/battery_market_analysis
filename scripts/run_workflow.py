#!/usr/bin/env python3
"""
Main workflow execution script - runs the complete agent pipeline
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config
from shared.logger import get_logger
from agents.supervisor.agent import SupervisorAgent
from retrieval.retriever import Retriever

logger = get_logger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("Battery Analysis System - Complete Workflow")
    logger.info("=" * 60)

    try:
        retriever = Retriever(
            vector_store_path=config.rag.vector_store_path,
            use_web_search=config.use_web_search,
        )

        supervisor = SupervisorAgent(retriever=retriever)

        logger.info("Starting workflow execution...")
        report = supervisor.run(save=True)

        if report:
            logger.info("Workflow completed successfully!")
            logger.info(f"Report length: {len(report)} chars")
            return 0
        else:
            logger.error("Workflow failed or no report generated")
            return 1

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
