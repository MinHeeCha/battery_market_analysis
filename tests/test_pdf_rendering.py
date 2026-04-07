"""Integration tests for PDF rendering module.

Tests the conversion of markdown reports from outputs/reports_md
to PDF format saved in outputs/reports_pdf.
"""

import pytest
from pathlib import Path

pytest.importorskip("reportlab")
from visualization.pdf_rendering import render_battery_report_pdf


class TestPDFRendering:
    """Test PDF rendering from actual markdown reports."""

    @pytest.fixture
    def reports_md_dir(self):
        """Return path to reports_md directory."""
        return Path(__file__).resolve().parent.parent / "outputs" / "reports_md"

    @pytest.fixture
    def reports_pdf_dir(self):
        """Return path to reports_pdf directory."""
        pdf_dir = Path(__file__).resolve().parent.parent / "outputs" / "reports_pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        return pdf_dir

    def test_render_markdown_report_to_pdf(self, reports_md_dir, reports_pdf_dir):
        """Test rendering a markdown report from reports_md to PDF."""
        # Find first markdown file
        md_files = list(reports_md_dir.glob("*.md"))
        assert len(md_files) > 0, "No markdown files found in reports_md"

        md_file = md_files[0]
        md_content = md_file.read_text(encoding="utf-8")
        assert len(md_content) > 0, f"Markdown file {md_file.name} is empty"

        # Generate output filename based on markdown filename
        pdf_filename = md_file.stem + ".pdf"
        pdf_path = reports_pdf_dir / pdf_filename

        # Render PDF
        rendered_path = render_battery_report_pdf(
            markdown_text=md_content, output_path=str(pdf_path)
        )

        # Verify PDF was created
        assert rendered_path.exists(), f"PDF not created at {rendered_path}"
        assert rendered_path.suffix.lower() == ".pdf"
        assert rendered_path.parent == reports_pdf_dir
        assert rendered_path.stat().st_size > 0, "PDF file is empty"

    def test_render_all_markdown_reports_to_pdf(self, reports_md_dir, reports_pdf_dir):
        """Test rendering all markdown reports to PDF."""
        md_files = list(reports_md_dir.glob("*.md"))
        if not md_files:
            pytest.skip("No markdown files found in reports_md")

        for md_file in md_files:
            md_content = md_file.read_text(encoding="utf-8")
            if not md_content.strip():
                continue

            pdf_filename = md_file.stem + ".pdf"
            pdf_path = reports_pdf_dir / pdf_filename

            rendered_path = render_battery_report_pdf(
                markdown_text=md_content, output_path=str(pdf_path)
            )

            assert rendered_path.exists()
            assert rendered_path.stat().st_size > 0
