"""PDF rendering module for battery strategy reports.

This module converts markdown-like Korean strategy reports into a styled PDF using
the project design system (red-orange palette, corporate typography, A4 layout,
header/footer navigation, KPI highlights, and section cards).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
	HRFlowable,
	KeepTogether,
	PageBreak,
	Paragraph,
	SimpleDocTemplate,
	Spacer,
	Table,
	TableStyle,
)


@dataclass(frozen=True)
class DesignTokens:
	"""Centralized design tokens for consistent styling."""

	brand_red: colors.Color = colors.HexColor("#E4002B")
	deep_red: colors.Color = colors.HexColor("#C00020")
	orange_red: colors.Color = colors.HexColor("#E8420A")
	bright_orange: colors.Color = colors.HexColor("#F07A00")
	golden_orange: colors.Color = colors.HexColor("#F5A623")
	warm_beige: colors.Color = colors.HexColor("#F5EDE0")
	dark_charcoal: colors.Color = colors.HexColor("#2D2D2D")
	medium_gray: colors.Color = colors.HexColor("#666666")
	light_gray: colors.Color = colors.HexColor("#E8E8E8")
	off_white: colors.Color = colors.HexColor("#F8F5F0")
	white: colors.Color = colors.HexColor("#FFFFFF")
	dark_beige_brown: colors.Color = colors.HexColor("#8B7355")


class BatteryReportPDFRenderer:
	"""Render battery market strategy markdown text into branded PDF."""

	def __init__(self, output_dir: str = "./outputs/reports_pdf"):
		self.output_dir = Path(output_dir)
		self.output_dir.mkdir(parents=True, exist_ok=True)
		self.tokens = DesignTokens()
		self._register_fonts()
		self.styles = self._build_styles()

	def render_from_markdown(self, markdown_text: str, output_filename: str) -> Path:
		"""Generate a styled PDF from report markdown text."""
		output_path = self.output_dir / output_filename
		sections = self._parse_sections(markdown_text)

		doc = SimpleDocTemplate(
			str(output_path),
			pagesize=A4,
			leftMargin=13 * mm,
			rightMargin=13 * mm,
			topMargin=15 * mm,
			bottomMargin=15 * mm,
			title="Battery Market Strategy Report",
		)

		story = self._build_story(sections)
		doc.build(story, onFirstPage=self._draw_header_footer, onLaterPages=self._draw_header_footer)
		return output_path

	def _register_fonts(self) -> None:
		"""Register optional Korean fonts; fall back to built-in fonts if unavailable."""
		font_candidates = [
			("NotoSansKR", "/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
			("NotoSansKR-Bold", "/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
		]
		for name, path in font_candidates:
			if Path(path).exists() and name not in pdfmetrics.getRegisteredFontNames():
				pdfmetrics.registerFont(TTFont(name, path))

	def _font(self, bold: bool = False) -> str:
		if bold and "NotoSansKR-Bold" in pdfmetrics.getRegisteredFontNames():
			return "NotoSansKR-Bold"
		if "NotoSansKR" in pdfmetrics.getRegisteredFontNames():
			return "NotoSansKR"
		return "Helvetica-Bold" if bold else "Helvetica"

	def _build_styles(self) -> StyleSheet1:
		styles = getSampleStyleSheet()
		styles.add(
			ParagraphStyle(
				name="TitleHero",
				parent=styles["Heading1"],
				fontName=self._font(True),
				fontSize=30,
				leading=34,
				textColor=self.tokens.dark_charcoal,
				alignment=TA_LEFT,
				spaceAfter=8,
			)
		)
		styles.add(
			ParagraphStyle(
				name="SectionHeader",
				parent=styles["Heading2"],
				fontName=self._font(True),
				fontSize=16,
				leading=20,
				textColor=self.tokens.brand_red,
				spaceBefore=10,
				spaceAfter=8,
			)
		)
		styles.add(
			ParagraphStyle(
				name="SubHeader",
				parent=styles["Heading3"],
				fontName=self._font(True),
				fontSize=12,
				leading=16,
				textColor=self.tokens.deep_red,
				spaceBefore=6,
				spaceAfter=4,
			)
		)
		styles.add(
			ParagraphStyle(
				name="BodyKR",
				parent=styles["BodyText"],
				fontName=self._font(False),
				fontSize=9.5,
				leading=16,
				textColor=self.tokens.dark_charcoal,
				alignment=TA_JUSTIFY,
				spaceAfter=5,
			)
		)
		styles.add(
			ParagraphStyle(
				name="Caption",
				parent=styles["BodyText"],
				fontName=self._font(False),
				fontSize=8,
				leading=11,
				textColor=self.tokens.medium_gray,
				alignment=TA_LEFT,
			)
		)
		styles.add(
			ParagraphStyle(
				name="KPIValue",
				parent=styles["Heading1"],
				fontName=self._font(True),
				fontSize=24,
				leading=26,
				textColor=self.tokens.brand_red,
				alignment=TA_CENTER,
			)
		)
		styles.add(
			ParagraphStyle(
				name="KPIText",
				parent=styles["BodyText"],
				fontName=self._font(False),
				fontSize=8,
				leading=10,
				textColor=self.tokens.medium_gray,
				alignment=TA_CENTER,
			)
		)
		return styles

	def _parse_sections(self, markdown_text: str) -> List[Tuple[str, List[Tuple[str, str]]]]:
		"""Parse markdown into section and block tuples.

		Returns:
			[(section_title, [(block_type, text), ...]), ...]
		"""
		lines = [line.rstrip() for line in markdown_text.splitlines()]
		sections: List[Tuple[str, List[Tuple[str, str]]]] = []

		current_title = ""
		current_blocks: List[Tuple[str, str]] = []

		for line in lines:
			if not line.strip():
				continue

			if line.startswith("## "):
				if current_title:
					sections.append((current_title, current_blocks))
				current_title = line[3:].strip()
				current_blocks = []
				continue

			if line.startswith("### "):
				current_blocks.append(("h3", line[4:].strip()))
				continue

			if line.startswith("**") and ":**" in line:
				current_blocks.append(("label", line.strip()))
				continue

			current_blocks.append(("p", line.strip()))

		if current_title:
			sections.append((current_title, current_blocks))
		return sections

	def _build_story(self, sections: Sequence[Tuple[str, List[Tuple[str, str]]]]) -> List:
		story: List = []

		story.append(Spacer(1, 10 * mm))
		story.append(Paragraph("배터리 시장 전략 비교 보고서", self.styles["TitleHero"]))
		story.append(Paragraph("BATTERY MARKET STRATEGY COMPARISON", self.styles["Caption"]))
		story.append(Spacer(1, 4 * mm))
		story.append(HRFlowable(thickness=1.2, color=self.tokens.brand_red, width="100%"))
		story.append(Spacer(1, 4 * mm))

		kpi_values = self._extract_kpis(sections)
		if kpi_values:
			story.append(self._build_kpi_row(kpi_values))
			story.append(Spacer(1, 4 * mm))

		for idx, (section_title, blocks) in enumerate(sections, start=1):
			story.append(self._section_banner(idx, section_title))
			for block_type, text in blocks:
				if block_type == "h3":
					story.append(Paragraph(text, self.styles["SubHeader"]))
				elif block_type == "label":
					story.append(self._label_card(text))
				else:
					story.append(Paragraph(self._clean_markdown(text), self.styles["BodyKR"]))

			if idx != len(sections):
				story.append(Spacer(1, 2 * mm))
				story.append(HRFlowable(thickness=0.6, color=self.tokens.light_gray, width="100%"))
				story.append(Spacer(1, 2 * mm))

			if idx in {2, 4}:
				story.append(PageBreak())

		return story

	def _extract_kpis(self, sections: Sequence[Tuple[str, List[Tuple[str, str]]]]) -> List[Tuple[str, str]]:
		kpis: List[Tuple[str, str]] = []
		joined = "\n".join(text for _, blocks in sections for _, text in blocks)

		for m in re.finditer(r"(\d{2,3}(?:,\d{3})*\s*억\s*달러)", joined):
			kpis.append((m.group(1), "시장 규모"))
			if len(kpis) >= 3:
				return kpis

		for m in re.finditer(r"(\d+\s*%\s*(?:이상|내외|수준)?)", joined):
			kpis.append((m.group(1), "성장/점유율 지표"))
			if len(kpis) >= 3:
				break

		return kpis[:3]

	def _build_kpi_row(self, kpis: Sequence[Tuple[str, str]]) -> Table:
		cells = []
		for value, label in kpis:
			cells.append(
				KeepTogether(
					[
						Paragraph(value, self.styles["KPIValue"]),
						Paragraph(label, self.styles["KPIText"]),
					]
				)
			)

		table = Table([cells], colWidths=[(A4[0] - 26 * mm) / max(len(cells), 1)] * max(len(cells), 1))
		table.setStyle(
			TableStyle(
				[
					("BACKGROUND", (0, 0), (-1, -1), self.tokens.warm_beige),
					("BOX", (0, 0), (-1, -1), 0, colors.transparent),
					("INNERGRID", (0, 0), (-1, -1), 0, colors.transparent),
					("LEFTPADDING", (0, 0), (-1, -1), 8),
					("RIGHTPADDING", (0, 0), (-1, -1), 8),
					("TOPPADDING", (0, 0), (-1, -1), 10),
					("BOTTOMPADDING", (0, 0), (-1, -1), 10),
				]
			)
		)
		return table

	def _section_banner(self, sec_no: int, title: str) -> Table:
		sec_label = f"Sec.{sec_no:02d}"
		left = Paragraph(f"<font color='#FFFFFF'><b>{sec_label}</b></font>", self.styles["Caption"])
		right = Paragraph(f"<font color='#FFFFFF'><b>{title.upper()}</b></font>", self.styles["SectionHeader"])
		table = Table([[left, right]], colWidths=[25 * mm, 150 * mm])
		table.setStyle(
			TableStyle(
				[
					("BACKGROUND", (0, 0), (-1, -1), self.tokens.brand_red),
					("TEXTCOLOR", (0, 0), (-1, -1), self.tokens.white),
					("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
					("LEFTPADDING", (0, 0), (-1, -1), 8),
					("RIGHTPADDING", (0, 0), (-1, -1), 8),
					("TOPPADDING", (0, 0), (-1, -1), 6),
					("BOTTOMPADDING", (0, 0), (-1, -1), 6),
				]
			)
		)
		return table

	def _label_card(self, text: str) -> Table:
		clean = self._clean_markdown(text)
		title, body = self._split_label_line(clean)
		content = [
			[Paragraph(f"<b>{title}</b>", self.styles["SubHeader"])],
			[Paragraph(body, self.styles["BodyKR"])],
		]
		table = Table(content, colWidths=[A4[0] - 26 * mm])
		table.setStyle(
			TableStyle(
				[
					("BACKGROUND", (0, 0), (-1, -1), self.tokens.off_white),
					("LINEBEFORE", (0, 0), (0, -1), 2, self.tokens.orange_red),
					("LEFTPADDING", (0, 0), (-1, -1), 8),
					("RIGHTPADDING", (0, 0), (-1, -1), 8),
					("TOPPADDING", (0, 0), (-1, -1), 5),
					("BOTTOMPADDING", (0, 0), (-1, -1), 5),
				]
			)
		)
		return table

	def _split_label_line(self, line: str) -> Tuple[str, str]:
		if ":" in line:
			k, v = line.split(":", 1)
			return k.strip(), v.strip()
		return "핵심", line

	def _clean_markdown(self, text: str) -> str:
		return text.replace("**", "").replace("`", "").strip()

	def _draw_header_footer(self, canvas, doc) -> None:
		width, height = A4
		canvas.saveState()

		header_y = height - 10 * mm
		canvas.setFont(self._font(False), 7.5)
		canvas.setFillColor(self.tokens.medium_gray)
		canvas.drawString(13 * mm, header_y, "Battery Strategy Report")

		tabs = "OVERVIEW   SUSTAINABILITY   PERFORMANCE   APPENDIX"
		canvas.drawCentredString(width / 2, header_y, tabs)

		canvas.setFillColor(self.tokens.brand_red)
		canvas.drawString(width - 30 * mm, header_y, f"{doc.page}")

		canvas.setStrokeColor(self.tokens.light_gray)
		canvas.setLineWidth(0.4)
		canvas.line(13 * mm, height - 12 * mm, width - 13 * mm, height - 12 * mm)

		footer_y = 9 * mm
		canvas.setFillColor(self.tokens.medium_gray)
		canvas.setFont(self._font(False), 7)
		canvas.drawString(13 * mm, footer_y, "MARKET INTELLIGENCE")
		canvas.drawRightString(width - 13 * mm, footer_y, "LGES vs CATL")

		canvas.restoreState()


def render_battery_report_pdf(markdown_text: str, output_path: str) -> Path:
	"""Convenience function used by scripts or workflows."""
	out = Path(output_path)
	renderer = BatteryReportPDFRenderer(output_dir=str(out.parent))
	return renderer.render_from_markdown(markdown_text=markdown_text, output_filename=out.name)
