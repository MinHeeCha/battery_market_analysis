"""
Structured PDF renderer for battery strategy reports.

Improved for:
- stable Korean font rendering using local webfont files (TTF/OTF)
- readable editorial hierarchy
- no overlapping hero text
- regular-weight body text
- safer summary numbering / reference layout
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@dataclass(frozen=True)
class DesignTokens:
    primary_red: colors.Color = colors.HexColor("#E4002B")
    deep_red: colors.Color = colors.HexColor("#C00020")
    orange: colors.Color = colors.HexColor("#F07A00")
    golden_orange: colors.Color = colors.HexColor("#F5A623")
    warm_beige: colors.Color = colors.HexColor("#F5EDE0")
    light_orange: colors.Color = colors.HexColor("#FFF3E0")
    brown: colors.Color = colors.HexColor("#8B7355")
    dark_charcoal: colors.Color = colors.HexColor("#2D2D2D")
    medium_gray: colors.Color = colors.HexColor("#666666")
    light_gray: colors.Color = colors.HexColor("#E0E0E0")
    off_white: colors.Color = colors.HexColor("#F8F5F0")
    white: colors.Color = colors.HexColor("#FFFFFF")
    page_number_gray: colors.Color = colors.HexColor("#999999")
    orange_red: colors.Color = colors.HexColor("#E8420A")
    appendix_start: colors.Color = colors.HexColor("#5A5A5A")
    appendix_end: colors.Color = colors.HexColor("#3A3A3A")


@dataclass
class ContentBlock:
    title: str
    body: str


@dataclass
class ParsedReport:
    title: str = "배터리 시장 전략 비교 보고서"
    generated_at: str = ""
    summary: List[ContentBlock] = field(default_factory=list)
    market: List[ContentBlock] = field(default_factory=list)
    lges: List[ContentBlock] = field(default_factory=list)
    catl: List[ContentBlock] = field(default_factory=list)
    comparison: List[ContentBlock] = field(default_factory=list)
    implications: str = ""
    references: List[str] = field(default_factory=list)


class GradientHero(Flowable):
    """Top hero/section intro panel with stable typography."""

    def __init__(
        self,
        renderer: "BatteryReportPDFRenderer",
        title: str,
        subtitle: str,
        label: str = "",
        height: float = 84 * mm,
        appendix: bool = False,
    ):
        super().__init__()
        self.renderer = renderer
        self.title = title
        self.subtitle = subtitle
        self.label = label
        self.height = height
        self.appendix = appendix
        self.width = 0

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height

    def draw(self):
        c = self.canv
        t = self.renderer.tokens
        w = self.width
        h = self.height

        if self.appendix:
            palette = [t.appendix_start, t.appendix_end]
        else:
            palette = [t.deep_red, t.primary_red, t.orange_red, t.orange, t.golden_orange]

        self.renderer._draw_gradient_rect(c, 0, 0, w, h, palette)

        # Left dark overlay for contrast
        overlay_w = min(w * 0.48, 120 * mm)
        c.setFillColor(colors.Color(t.deep_red.red, t.deep_red.green, t.deep_red.blue, alpha=0.38))
        c.rect(0, 0, overlay_w, h, stroke=0, fill=1)

        self.renderer._draw_wave_overlay(c, w, h)

        c.setFillColor(t.white)
        font_name = self.renderer._font(True)

        left = 18
        top = h - 18
        text_width = min(w * 0.42, 105 * mm)

        if h >= 70 * mm:
            label_size = 10
            title_size = self.renderer._fit_font_size(self.title, font_name, 40, 24, text_width)
            subtitle_size = 11
            title_gap = 20
            subtitle_gap = 14
        else:
            label_size = 9
            title_size = self.renderer._fit_font_size(self.title, font_name, 24, 18, text_width)
            subtitle_size = 10
            title_gap = 14
            subtitle_gap = 12

        if self.label:
            c.setFont(font_name, label_size)
            c.drawString(left, top, self.label)

        c.setFont(font_name, title_size)
        title_y = top - label_size - title_gap
        c.drawString(left, title_y, self.title)

        c.setFont(self.renderer._font(False), subtitle_size)
        subtitle_y = max(12, title_y - subtitle_gap)
        c.drawString(left, subtitle_y, self.subtitle)


class ChartPlaceholder(Flowable):
    """Simple chart placeholder panel."""

    def __init__(
        self,
        renderer: "BatteryReportPDFRenderer",
        title: str,
        caption: str,
        variant: str,
        accent: Optional[colors.Color] = None,
        height: float = 70 * mm,
    ):
        super().__init__()
        self.renderer = renderer
        self.title = title
        self.caption = caption
        self.variant = variant
        self.accent = accent or renderer.tokens.primary_red
        self.height = height
        self.width = 0

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height

    def draw(self):
        c = self.canv
        t = self.renderer.tokens
        w = self.width
        h = self.height

        c.setFillColor(t.white)
        c.setStrokeColor(t.light_gray)
        c.setLineWidth(0.7)
        c.rect(0, 0, w, h, stroke=1, fill=1)

        c.setFillColor(t.primary_red)
        c.rect(0, h - 6, w, 6, stroke=0, fill=1)

        c.setFillColor(t.dark_charcoal)
        c.setFont(self.renderer._font(True), 11)
        c.drawString(14, h - 20, self.title)

        c.setFillColor(t.medium_gray)
        c.setFont(self.renderer._font(False), 7.5)
        c.drawString(14, 12, self.caption[:110])

        plot_x = 16
        plot_y = 22
        plot_w = w - 32
        plot_h = h - 44

        c.setStrokeColor(t.light_gray)
        c.setLineWidth(0.6)
        c.line(plot_x, plot_y, plot_x, plot_y + plot_h - 8)
        c.line(plot_x, plot_y, plot_x + plot_w, plot_y)

        if self.variant == "line":
            self._draw_line_chart(c, plot_x, plot_y, plot_w, plot_h)
        else:
            self._draw_stacked_bars(c, plot_x, plot_y, plot_w, plot_h)

    def _draw_line_chart(self, c, x, y, w, h):
        t = self.renderer.tokens
        pts = [
            (x + 10, y + 16),
            (x + w * 0.28, y + 32),
            (x + w * 0.52, y + 54),
            (x + w * 0.74, y + 70),
            (x + w - 8, y + 92),
        ]
        c.setStrokeColor(self.accent)
        c.setLineWidth(2.2)
        for idx in range(len(pts) - 1):
            c.line(pts[idx][0], pts[idx][1], pts[idx + 1][0], pts[idx + 1][1])

        c.setFillColor(self.accent)
        for px, py in pts:
            c.circle(px, py, 2.7, stroke=0, fill=1)

        c.setFillColor(t.medium_gray)
        c.setFont(self.renderer._font(False), 7)
        c.drawString(x + 6, y - 10, "2023")
        c.drawCentredString(x + w * 0.52, y - 10, "2026")
        c.drawRightString(x + w, y - 10, "2030")
        c.drawRightString(x + w - 6, y + 96, "CAGR 15%+")

    def _draw_stacked_bars(self, c, x, y, w, h):
        t = self.renderer.tokens
        labels = ["EV", "Hybrid", "ESS"]
        values = [(0.55, 0.22, 0.23), (0.42, 0.18, 0.40), (0.34, 0.16, 0.50)]
        colorset = [t.primary_red, t.orange, t.golden_orange]
        bar_w = w / 6

        for idx, stack in enumerate(values):
            left = x + 22 + idx * (bar_w + 22)
            bottom = y + 8
            total_h = h - 30
            for seg_idx, ratio in enumerate(stack):
                seg_h = total_h * ratio
                c.setFillColor(colorset[seg_idx])
                c.rect(left, bottom, bar_w, seg_h, stroke=0, fill=1)
                bottom += seg_h
            c.setFillColor(t.medium_gray)
            c.setFont(self.renderer._font(False), 7)
            c.drawCentredString(left + bar_w / 2, y - 10, labels[idx])


class BatteryReportPDFRenderer:
    """Render markdown reports into structured editorial PDFs."""

    def __init__(self, output_dir: str = "./outputs/reports_pdf"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tokens = DesignTokens()
        self.page_width, self.page_height = A4
        self.content_width = self.page_width - 26 * mm
        self._register_fonts()
        self.styles = self._build_styles()

    def render_from_markdown(self, markdown_text: str, output_filename: str) -> Path:
        output_path = self.output_dir / output_filename
        report = self._parse_report(markdown_text)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=13 * mm,
            rightMargin=13 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title=report.title,
        )

        story = self._build_story(report)
        doc.build(story, onFirstPage=self._draw_cover_page_frame, onLaterPages=self._draw_page_frame)
        return output_path

    def _register_fonts(self) -> None:
        """
        Prefer local downloaded webfont files:
        assets/fonts/NotoSansKR-Regular.ttf
        assets/fonts/NotoSansKR-Bold.ttf
        """
        project_root = Path.cwd()

        regular_candidates = [
            project_root / "assets/fonts/NotoSansKR-Regular.ttf",
            project_root / "assets/fonts/NotoSansKR-Regular.otf",
            Path("/System/Library/Fonts/Supplemental/NotoSansKR-Regular.otf"),
            Path("/Library/Fonts/NotoSansKR-Regular.otf"),
            Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
        ]
        bold_candidates = [
            project_root / "assets/fonts/NotoSansKR-Bold.ttf",
            project_root / "assets/fonts/NotoSansKR-Bold.otf",
            Path("/System/Library/Fonts/Supplemental/NotoSansKR-Bold.otf"),
            Path("/Library/Fonts/NotoSansKR-Bold.otf"),
            Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
        ]

        self._register_font_family("NotoSansKR", regular_candidates)
        self._register_font_family("NotoSansKR-Bold", bold_candidates)

    def _register_font_family(self, name: str, candidates: Sequence[Path]) -> None:
        if name in pdfmetrics.getRegisteredFontNames():
            return

        for path in candidates:
            try:
                if path.exists():
                    pdfmetrics.registerFont(TTFont(name, str(path)))
                    return
            except Exception:
                continue

    def _font(self, bold: bool = False, display: bool = False) -> str:
        if bold and "NotoSansKR-Bold" in pdfmetrics.getRegisteredFontNames():
            return "NotoSansKR-Bold"
        if not bold and "NotoSansKR" in pdfmetrics.getRegisteredFontNames():
            return "NotoSansKR"
        if display:
            return "Helvetica-Bold"
        return "Helvetica-Bold" if bold else "Helvetica"

    def _build_styles(self) -> StyleSheet1:
        styles = getSampleStyleSheet()
        add = styles.add
        t = self.tokens

        add(
            ParagraphStyle(
                name="PageTitle",
                parent=styles["Heading1"],
                fontName=self._font(True),
                fontSize=28,
                leading=31,
                textColor=t.dark_charcoal,
                alignment=TA_LEFT,
                spaceAfter=24,
            )
        )
        add(
            ParagraphStyle(
                name="RedSubTitle",
                parent=styles["Heading2"],
                fontName=self._font(True),
                fontSize=15,
                leading=19,
                textColor=t.primary_red,
                alignment=TA_LEFT,
                spaceAfter=6,
            )
        )
        add(
            ParagraphStyle(
                name="Body",
                parent=styles["BodyText"],
                fontName=self._font(False),
                fontSize=9.5,
                leading=16.6,
                textColor=t.dark_charcoal,
                alignment=TA_LEFT,
                spaceAfter=12,
            )
        )
        add(
            ParagraphStyle(
                name="BodyMuted",
                parent=styles["BodyText"],
                fontName=self._font(False),
                fontSize=8.6,
                leading=14.2,
                textColor=t.medium_gray,
                alignment=TA_LEFT,
                spaceAfter=10,
            )
        )
        add(
            ParagraphStyle(
                name="Caption",
                parent=styles["BodyText"],
                fontName=self._font(False),
                fontSize=7.5,
                leading=10,
                textColor=t.medium_gray,
                alignment=TA_LEFT,
            )
        )
        add(
            ParagraphStyle(
                name="CardKicker",
                parent=styles["BodyText"],
                fontName=self._font(True),
                fontSize=8,
                leading=10,
                textColor=t.medium_gray,
                alignment=TA_LEFT,
                spaceAfter=4,
            )
        )
        add(
            ParagraphStyle(
                name="IndexLabel",
                parent=styles["BodyText"],
                fontName=self._font(False),
                fontSize=9,
                leading=10,
                textColor=t.medium_gray,
                alignment=TA_CENTER,
                spaceAfter=0,
            )
        )
        add(
            ParagraphStyle(
                name="KPIValue",
                parent=styles["Heading1"],
                fontName=self._font(True),
                fontSize=48,
                leading=52,
                textColor=t.primary_red,
                alignment=TA_CENTER,
            )
        )
        add(
            ParagraphStyle(
                name="KPIUnit",
                parent=styles["BodyText"],
                fontName=self._font(True),
                fontSize=18,
                leading=20,
                textColor=t.primary_red,
                alignment=TA_CENTER,
            )
        )
        add(
            ParagraphStyle(
                name="KPIDescription",
                parent=styles["BodyText"],
                fontName=self._font(False),
                fontSize=8.2,
                leading=11,
                textColor=t.medium_gray,
                alignment=TA_CENTER,
            )
        )
        add(
            ParagraphStyle(
                name="Reference",
                parent=styles["BodyText"],
                fontName=self._font(False),
                fontSize=7.8,
                leading=10.6,
                textColor=t.dark_charcoal,
                alignment=TA_LEFT,
                spaceAfter=6,
            )
        )
        add(
            ParagraphStyle(
                name="SWOTLabel",
                parent=styles["Heading3"],
                fontName=self._font(True),
                fontSize=11,
                leading=13,
                textColor=t.primary_red,
                alignment=TA_LEFT,
                spaceAfter=4,
            )
        )
        return styles

    def _parse_report(self, markdown_text: str) -> ParsedReport:
        report = ParsedReport()
        current_section: Optional[str] = None
        current_subtitle: Optional[str] = None
        current_body: List[str] = []

        def commit_block() -> None:
            nonlocal current_subtitle, current_body, current_section
            if not current_section or current_subtitle is None:
                return
            body = " ".join(part.strip() for part in current_body if part.strip()).strip()
            body = re.sub(r"\s+", " ", body)
            target = getattr(report, current_section)
            if isinstance(target, list):
                target.append(ContentBlock(title=current_subtitle, body=body))
            current_subtitle = None
            current_body = []

        section_map = {
            "1. SUMMARY": "summary",
            "2. 시장 배경": "market",
            "3. LG에너지솔루션 전략 분석": "lges",
            "4. CATL 전략 분석": "catl",
            "5. 전략 비교 및 Comparative SWOT": "comparison",
            "6. 종합 시사점": "implications",
            "7. REFERENCES": "references",
            "7. References": "references",
        }

        for raw in markdown_text.splitlines():
            line = raw.strip()
            if not line:
                continue

            if line.startswith("# "):
                report.title = line[2:].strip()
                continue

            if line.startswith("> 생성일시:"):
                report.generated_at = line.replace("> 생성일시:", "").strip()
                continue

            if line.startswith("## "):
                commit_block()
                section_title = line[3:].strip()
                current_section = section_map.get(section_title)
                current_subtitle = None
                current_body = []
                continue

            if current_section == "references" and line.startswith("- "):
                report.references.append(line[2:].strip())
                continue

            if current_section == "implications":
                report.implications = f"{report.implications} {line}".strip()
                continue

            if line.startswith("### "):
                commit_block()
                current_subtitle = line[4:].strip()
                current_body = []
                continue

            label_match = re.match(r"^\*\*(.+?)\*\*\s*$", line)
            if current_section == "summary" and label_match:
                commit_block()
                current_subtitle = label_match.group(1).strip()
                current_body = []
                continue

            if current_subtitle is None and current_section in {"market", "lges", "catl", "comparison"}:
                current_subtitle = "핵심 내용"
            current_body.append(line.replace("**", "").strip())

        commit_block()
        return report

    def _build_story(self, report: ParsedReport) -> List:
        story: List = []

        story.extend(self._build_cover_summary_page(report))
        if report.market:
            story.append(PageBreak())
            story.extend(self._build_market_page(report))
        if report.lges:
            story.append(PageBreak())
            story.extend(self._build_company_page(company_name="LG에너지솔루션", blocks=report.lges))
        if report.catl:
            story.append(PageBreak())
            story.extend(self._build_company_page(company_name="CATL", blocks=report.catl))
        if report.comparison or report.implications:
            story.append(PageBreak())
            story.extend(self._build_swot_page(report))
        if report.references:
            story.append(PageBreak())
            story.extend(self._build_references_page(report))

        return story

    def _build_cover_summary_page(self, report: ParsedReport) -> List:
        story: List = []
        story.append(
            GradientHero(
                self,
                title="BATTERY",
                subtitle=report.generated_at or "Battery market strategy report",
                label="BATTERY MARKET STRATEGY REPORT",
                height=82 * mm,
            )
        )
        story.append(Spacer(1, 8 * mm))

        if report.summary:
            story.append(self._summary_box(report.summary))
            story.append(Spacer(1, 6 * mm))

        return story

    def _build_market_page(self, report: ParsedReport) -> List:
        story: List = []
        story.append(
            GradientHero(
                self,
                title="MARKET",
                subtitle="시장 배경과 외부 환경 변화",
                label="SECTION 02",
                height=35 * mm,
            )
        )
        story.append(Spacer(1, 7 * mm))
        story.append(Paragraph("시장 배경", self.styles["PageTitle"]))

        market_cards = self._make_card_grid(report.market, columns=1, tone="content")
        story.append(market_cards)
        return story

    def _build_company_page(self, company_name: str, blocks: Sequence[ContentBlock]) -> List:
        story: List = []
        story.append(
            GradientHero(
                self,
                title=company_name,
                subtitle=f"{company_name} 전략 구조와 대응 방향",
                label="COMPANY ANALYSIS",
                height=35 * mm,
            )
        )
        story.append(Spacer(1, 7 * mm))
        story.append(Paragraph(f"{company_name} 전략 분석", self.styles["PageTitle"]))
        story.append(self._mini_fact_strip(blocks))
        story.append(Spacer(1, 6 * mm))
        story.append(self._make_card_grid(blocks, columns=2, tone="content"))
        return story

    def _build_swot_page(self, report: ParsedReport) -> List:
        story: List = []
        story.append(
            GradientHero(
                self,
                title="SWOT",
                subtitle="기업별 SWOT과 시사점",
                label="COMPARATIVE FRAME",
                height=35 * mm,
            )
        )
        story.append(Spacer(1, 7 * mm))
        story.append(Paragraph("전략 비교 및 Comparative SWOT", self.styles["PageTitle"]))

        comparison_map = {block.title: block.body for block in report.comparison}
        lges_swot = self._parse_swot_text(comparison_map.get("5.2 LG에너지솔루션 SWOT", ""))
        catl_swot = self._parse_swot_text(comparison_map.get("5.3 CATL SWOT", ""))

        swot_table = Table(
            [[
                self._swot_company_panel("LG에너지솔루션", lges_swot),
                self._swot_company_panel("CATL", catl_swot),
            ]],
            colWidths=[(self.content_width - 24) / 2, (self.content_width - 24) / 2],
        )
        swot_table.setStyle(
            TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 24),
            ])
        )
        story.append(swot_table)
        story.append(Spacer(1, 6 * mm))

        bottom_cards = [
            ContentBlock("핵심 전략 비교", comparison_map.get("5.1 핵심 전략 비교", "")),
            ContentBlock("Comparative SWOT", comparison_map.get("5.4 Comparative SWOT", "")),
            ContentBlock("종합 시사점", report.implications),
        ]
        story.append(self._make_card_grid(bottom_cards, columns=3, tone="insight"))
        return story

    def _build_references_page(self, report: ParsedReport) -> List:
        story: List = []
        story.append(
            GradientHero(
                self,
                title="APPENDIX",
                subtitle="Sources and references",
                label="APPENDIX",
                height=35 * mm,
                appendix=True,
            )
        )
        story.append(Spacer(1, 7 * mm))
        story.append(Paragraph("References", self.styles["PageTitle"]))

        rows = []
        for idx, ref in enumerate(report.references, start=1):
            rows.append(
                [
                    Paragraph(f"<para align='center'>{idx:02d}</para>", self.styles["IndexLabel"]),
                    Paragraph(self._format_reference(ref), self.styles["Reference"]),
                ]
            )

        table = Table(rows, colWidths=[16 * mm, self.content_width - 16 * mm], repeatRows=0)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.tokens.white),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.tokens.light_gray),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, self.tokens.light_gray),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(table)
        return story

    def _make_card_grid(self, blocks: Sequence[ContentBlock], columns: int, tone: str) -> Table:
        valid = [block for block in blocks if block.body]
        rows = []
        gutter = 24 if columns == 2 else 16
        col_width = (self.content_width - gutter * (columns - 1)) / columns

        for start in range(0, len(valid), columns):
            chunk = list(valid[start : start + columns])
            while len(chunk) < columns:
                chunk.append(ContentBlock("", ""))
            rows.append([self._content_card(block, tone=tone, width=col_width) for block in chunk])

        table = Table(rows, colWidths=[col_width] * columns)
        style = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), gutter),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ]
        for row_idx in range(len(rows)):
            style.append(("RIGHTPADDING", (columns - 1, row_idx), (columns - 1, row_idx), 0))
        table.setStyle(TableStyle(style))
        return table

    def _content_card(self, block: ContentBlock, tone: str, width: float) -> Table:
        if not block.title and not block.body:
            blank = Table([[""]], colWidths=[width], rowHeights=[1])
            blank.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0, colors.transparent)]))
            return blank

        if tone == "summary":
            fill = self.tokens.white
            accent = self.tokens.primary_red
        elif tone == "insight":
            fill = self.tokens.light_orange
            accent = self.tokens.orange
        else:
            fill = self.tokens.white
            accent = self.tokens.primary_red

        body_text = self._paragraphize(block.body)
        data = [
            [Paragraph("SUMMARY" if tone == "summary" else "KEY POINT", self.styles["CardKicker"])],
            [Paragraph(self._escape(block.title), self.styles["RedSubTitle"])],
            [Paragraph(body_text, self.styles["Body"])],
        ]
        table = Table(data, colWidths=[width])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), fill),
                    ("LINEBEFORE", (0, 0), (0, -1), 2, accent),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.tokens.light_gray),
                    ("LEFTPADDING", (0, 0), (-1, -1), 24),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 24),
                    ("TOPPADDING", (0, 0), (-1, -1), 20),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return table

    def _build_kpi_row(self, kpis: Sequence[Tuple[str, str]]) -> Table:
        ordered = sorted(kpis, key=lambda item: len(item[0]), reverse=True)
        col_width = (self.content_width - 16 * (len(ordered) - 1)) / len(ordered)
        cells = [self._kpi_card(value, label, col_width) for value, label in ordered]
        table = Table([cells], colWidths=[col_width] * len(cells))
        style = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
        style.append(("RIGHTPADDING", (len(cells) - 1, 0), (len(cells) - 1, 0), 0))
        table.setStyle(TableStyle(style))
        return table

    def _kpi_card(self, value: str, label: str, width: float) -> Table:
        number, unit = self._split_kpi_value(value)
        negative = any(marker in value for marker in ["감소", "하락", "-"])
        number_size = 42 if len(number) >= 4 else 48
        value_style = ParagraphStyle(
            "KPIValueNegative" if negative else "KPIValuePositive",
            parent=self.styles["KPIValue"],
            fontSize=number_size,
            leading=number_size + 4,
            textColor=self.tokens.brown if negative else self.tokens.primary_red,
        )
        unit_style = ParagraphStyle(
            "KPIUnitNegative" if negative else "KPIUnitPositive",
            parent=self.styles["KPIUnit"],
            textColor=self.tokens.brown if negative else self.tokens.primary_red,
        )
        data = [
            [Paragraph(number, value_style)],
            [Paragraph(unit or "&nbsp;", unit_style)],
            [Paragraph(self._escape(label), self.styles["KPIDescription"])],
        ]
        table = Table(data, colWidths=[width])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.tokens.warm_beige),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.tokens.light_gray),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return table

    def _summary_box(self, blocks: Sequence[ContentBlock]) -> Table:
        rows: List[List[Paragraph]] = []
        for idx, block in enumerate(blocks, start=1):
            label = Paragraph(f"<para align='center'>{idx:02d}</para>", self.styles["IndexLabel"])
            title = Paragraph(self._escape(block.title), self.styles["RedSubTitle"])
            body = Paragraph(self._paragraphize(block.body), self.styles["Body"])
            rows.extend([[label, title], ["", body]])

        table = Table(rows, colWidths=[16 * mm, self.content_width - 16 * mm])
        style = [
            ("BACKGROUND", (0, 0), (-1, -1), self.tokens.off_white),
            ("BOX", (0, 0), (-1, -1), 0.8, self.tokens.light_gray),
            ("LINEBEFORE", (0, 0), (0, -1), 2, self.tokens.primary_red),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        for row_idx in range(1, len(rows), 2):
            style.append(("LINEBELOW", (0, row_idx), (-1, row_idx), 0.4, self.tokens.light_gray))
            style.append(("BOTTOMPADDING", (0, row_idx), (-1, row_idx), 14))
        table.setStyle(TableStyle(style))
        return table

    def _mini_fact_strip(self, blocks: Sequence[ContentBlock]) -> Table:
        facts = []
        for block in blocks[:3]:
            facts.append(
                Table(
                    [
                        [Paragraph(self._escape(block.title), self.styles["CardKicker"])],
                        [Paragraph(self._short_caption(block.body, 95), self.styles["BodyMuted"])],
                    ],
                    colWidths=[(self.content_width - 32) / 3],
                )
            )

        while len(facts) < 3:
            facts.append(Table([[""]], colWidths=[(self.content_width - 32) / 3]))

        table = Table([facts], colWidths=[(self.content_width - 32) / 3] * 3)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.tokens.white),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.tokens.light_gray),
                    ("INNERGRID", (0, 0), (-1, -1), 0.6, self.tokens.light_gray),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return table

    def _swot_company_panel(self, company_name: str, swot: Dict[str, str]) -> Table:
        cells = [
            self._swot_cell("S", "Strength", swot.get("S", "")),
            self._swot_cell("W", "Weakness", swot.get("W", "")),
            self._swot_cell("O", "Opportunity", swot.get("O", "")),
            self._swot_cell("T", "Threat", swot.get("T", "")),
        ]
        inner = Table(
            [[cells[0], cells[1]], [cells[2], cells[3]]],
            colWidths=[(self.content_width - 36) / 4, (self.content_width - 36) / 4],
        )
        inner.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )

        outer = Table(
            [
                [Paragraph(company_name, self.styles["RedSubTitle"])],
                [inner],
            ],
            colWidths=[(self.content_width - 24) / 2],
        )
        outer.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.tokens.white),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.tokens.light_gray),
                    ("LINEBEFORE", (0, 0), (0, -1), 2, self.tokens.primary_red),
                    ("LEFTPADDING", (0, 0), (-1, -1), 16),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                    ("TOPPADDING", (0, 0), (-1, -1), 16),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return outer

    def _swot_cell(self, letter: str, title: str, body: str) -> Table:
        fill_map = {
            "S": self.tokens.off_white,
            "W": self.tokens.warm_beige,
            "O": self.tokens.light_orange,
            "T": colors.HexColor("#F9F4EC"),
        }
        label_color = self.tokens.primary_red if letter in {"S", "O"} else self.tokens.brown
        label = Paragraph(
            f"<font color='{self._color_hex(label_color)}'><b>{letter}</b></font> {self._escape(title)}",
            self.styles["SWOTLabel"],
        )
        body_para = Paragraph(self._paragraphize(body or "(내용 없음)"), self.styles["BodyMuted"])
        table = Table([[label], [body_para]], colWidths=[(self.content_width - 36) / 4])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), fill_map[letter]),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.tokens.light_gray),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        return table

    def _parse_swot_text(self, text: str) -> Dict[str, str]:
        text = text.replace("강점(S)", "S").replace("약점(W)", "W").replace("기회(O)", "O").replace("위협(T)", "T")
        pattern = re.compile(r"(S|W|O|T)\s*:\s*(.*?)(?=(?:\s+[SWOT]\s*:)|$)")
        parsed = {key: value.strip() for key, value in pattern.findall(text)}
        return parsed

    def _split_kpi_value(self, value: str) -> Tuple[str, str]:
        tokens = value.split()
        if len(tokens) >= 2:
            return tokens[0], " ".join(tokens[1:])
        match = re.match(r"(\d+(?:,\d+)*(?:\.\d+)?)(.*)", value)
        if match:
            return match.group(1), match.group(2).strip()
        return value, ""

    def _format_reference(self, ref: str) -> str:
        ref = ref.replace("data/raw/", "")
        ref = re.sub(r"https?://[^\s]+", lambda m: self._domain_only(m.group(0)), ref)
        ref = ref.replace("*. ", "")
        ref = re.sub(r"\s+", " ", ref).strip()
        ref = ref.replace("[PDF] ", "").replace("*", "")
        if len(ref) > 160:
            ref = ref[:157].rstrip() + "..."
        return self._escape(ref)

    def _domain_only(self, url: str) -> str:
        clean = re.sub(r"^https?://", "", url)
        return clean.split("/")[0]

    def _short_caption(self, text: str, limit: int) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= limit:
            return text
        cut = text[:limit].rsplit(" ", 1)[0].strip()
        return f"{cut}..."

    def _paragraphize(self, text: str) -> str:
        clean = self._escape(re.sub(r"\s+", " ", text).strip())
        clean = clean.replace("• ", "<br/>• ")
        clean = clean.replace("- ", "<br/>- ")
        return clean

    def _escape(self, text: str) -> str:
        return escape(text or "")

    def _color_hex(self, color: colors.Color) -> str:
        return "#" + color.hexval().lower().replace("0x", "")

    def _draw_gradient_rect(self, canvas, x, y, width, height, palette: Sequence[colors.Color]) -> None:
        # horizontal gradient
        steps = 100
        for idx in range(steps):
            ratio = idx / max(steps - 1, 1)
            color = self._sample_gradient(palette, ratio)
            canvas.setFillColor(color)
            canvas.rect(x + ratio * width, y, width / steps + 1, height, stroke=0, fill=1)

    def _sample_gradient(self, palette: Sequence[colors.Color], ratio: float) -> colors.Color:
        if len(palette) == 1:
            return palette[0]
        ratio = max(0.0, min(1.0, ratio))
        seg = ratio * (len(palette) - 1)
        left_idx = int(seg)
        right_idx = min(left_idx + 1, len(palette) - 1)
        local = seg - left_idx
        left = palette[left_idx]
        right = palette[right_idx]
        return colors.Color(
            left.red + (right.red - left.red) * local,
            left.green + (right.green - left.green) * local,
            left.blue + (right.blue - left.blue) * local,
        )

    def _draw_wave_overlay(self, canvas, width: float, height: float) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.Color(1, 1, 1, alpha=0.12))
        canvas.setLineWidth(18)
        canvas.bezier(
            width * 0.42, height * 0.12,
            width * 0.60, height * 0.34,
            width * 0.72, height * 0.08,
            width * 0.98, height * 0.28,
        )
        canvas.setStrokeColor(colors.Color(1, 1, 1, alpha=0.08))
        canvas.setLineWidth(10)
        canvas.bezier(
            width * 0.34, height * 0.66,
            width * 0.52, height * 0.86,
            width * 0.74, height * 0.58,
            width * 0.98, height * 0.78,
        )
        canvas.restoreState()

    def _fit_font_size(self, text: str, font_name: str, max_size: float, min_size: float, max_width: float) -> float:
        size = max_size
        while size > min_size and pdfmetrics.stringWidth(text, font_name, size) > max_width:
            size -= 0.5
        return max(size, min_size)

    def _draw_cover_page_frame(self, canvas, doc) -> None:
        self._draw_page_background(canvas)
        self._draw_page_number(canvas, doc.page)

    def _draw_page_frame(self, canvas, doc) -> None:
        self._draw_page_background(canvas)
        self._draw_page_number(canvas, doc.page)

    def _draw_page_background(self, canvas) -> None:
        canvas.saveState()
        canvas.setFillColor(self.tokens.white)
        canvas.rect(0, 0, self.page_width, self.page_height, stroke=0, fill=1)
        canvas.setStrokeColor(self.tokens.light_gray)
        canvas.setLineWidth(0.4)
        canvas.line(13 * mm, self.page_height - 12 * mm, self.page_width - 13 * mm, self.page_height - 12 * mm)
        canvas.restoreState()

    def _draw_page_number(self, canvas, page_no: int) -> None:
        canvas.saveState()
        canvas.setFont(self._font(False), 9)
        canvas.setFillColor(self.tokens.page_number_gray)
        canvas.drawRightString(self.page_width - 13 * mm, self.page_height - 8 * mm, str(page_no))
        canvas.restoreState()


def render_battery_report_pdf(markdown_text: str, output_path: str) -> Path:
    out = Path(output_path)
    renderer = BatteryReportPDFRenderer(output_dir=str(out.parent))
    return renderer.render_from_markdown(markdown_text=markdown_text, output_filename=out.name)