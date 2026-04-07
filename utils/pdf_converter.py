"""
PDF converter - converts markdown to PDF
"""
from pathlib import Path
from shared.logger import get_logger

logger = get_logger(__name__)


class PDFConverter:
    """Converts markdown report content to styled PDF format."""
    
    def __init__(self, output_dir: str = "./outputs/reports_pdf"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_md_to_pdf(self, md_content: str, output_filename: str = None) -> Path:
        """Convert markdown content to a styled PDF report."""
        from datetime import datetime

        from visualization.pdf_rendering import render_battery_report_pdf
        
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"battery_strategy_report_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename

        logger.info(f"Rendering PDF report: {output_path}")
        rendered_path = render_battery_report_pdf(markdown_text=md_content, output_path=str(output_path))
        logger.info(f"PDF rendered successfully: {rendered_path}")
        return rendered_path
