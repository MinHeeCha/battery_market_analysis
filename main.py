#!/usr/bin/env python3
"""Run full supervisor workflow and generate markdown + PDF in one command.

Usage:
	python main.py
	python main.py --no-save-md
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents.supervisor.agent import SupervisorAgent
from retrieval.retriever import Retriever
from shared.logger import get_logger
from visualization.pdf_rendering import render_battery_report_pdf


logger = get_logger(__name__)


def run_pipeline(save_md: bool = True) -> int:
	"""Execute supervisor workflow and convert final markdown to PDF."""
	try:
		logger.info("=" * 60)
		logger.info("Battery Analysis: Supervisor -> Markdown -> PDF")
		logger.info("=" * 60)

		vector_store_path = ROOT / "data" / "vector_store"
		retriever = Retriever(vector_store_path=str(vector_store_path))

		info = retriever.get_embedder_info()
		if not info.get("vector_store_ready", False):
			logger.error("Vector store is not ready: %s", vector_store_path)
			logger.error("Run: python scripts/ingest_documents.py --reset")
			return 1
		if info.get("collection_count", 0) == 0:
			logger.error("Vector store is empty: %s", vector_store_path)
			logger.error("Run: python scripts/ingest_documents.py --reset")
			return 1

		supervisor = SupervisorAgent(retriever=retriever)
		final_md = supervisor.run(save=save_md)

		if not final_md or len(final_md.strip()) == 0:
			logger.error("Supervisor returned an empty markdown report")
			return 1

		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

		md_path = ROOT / "outputs" / "reports_md" / f"battery_report_{timestamp}.md"
		md_path.parent.mkdir(parents=True, exist_ok=True)
		if not save_md:
			md_path.write_text(final_md, encoding="utf-8")
			logger.info("Markdown report saved -> %s", md_path)
		else:
			logger.info("Markdown report saved by supervisor (save=True)")

		pdf_path = ROOT / "outputs" / "reports_pdf" / f"battery_report_{timestamp}.pdf"
		pdf_path.parent.mkdir(parents=True, exist_ok=True)
		rendered_pdf = render_battery_report_pdf(markdown_text=final_md, output_path=str(pdf_path))

		logger.info("PDF report saved -> %s", rendered_pdf)
		logger.info("Pipeline completed successfully")
		return 0

	except Exception as exc:
		logger.error("Pipeline failed: %s", exc, exc_info=True)
		return 1


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Run full supervisor workflow and generate PDF from final markdown."
	)
	parser.add_argument(
		"--no-save-md",
		action="store_true",
		help="Disable supervisor markdown save and save markdown in main.py only.",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = parse_args()
	raise SystemExit(run_pipeline(save_md=not args.no_save_md))
