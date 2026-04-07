"""Market research visualization generator.

Generates PNG assets from market analysis text so the PDF renderer can embed
charts in the market section.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import matplotlib

# Use headless backend for terminal/server environments.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager


class MarketResearchVisualizer:
    """Generate lightweight market charts from analysis output."""

    def __init__(self, output_dir: str = "./visualization"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated_files: List[str] = []
        self._setup_plot_style()

    def _setup_plot_style(self) -> None:
        """Configure chart style and try a Korean-capable font first."""
        preferred_fonts = ["AppleGothic", "Malgun Gothic", "NanumGothic", "DejaVu Sans"]
        available = {f.name for f in font_manager.fontManager.ttflist}
        selected = next((name for name in preferred_fonts if name in available), "DejaVu Sans")

        plt.rcParams["font.family"] = selected
        plt.rcParams["axes.unicode_minus"] = False
        plt.rcParams["figure.facecolor"] = "white"

    def visualize_market_research(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Create core PNG visualizations and return absolute paths."""
        self.generated_files = []
        analysis_text = str(analysis_result.get("final_answer", ""))

        self._generate_keyword_bar_chart(analysis_text)
        self._generate_priority_radar_like_chart(analysis_text)

        return self.generated_files

    def _generate_keyword_bar_chart(self, analysis_text: str) -> None:
        labels = ["EV 캐즘", "수요 구조", "정책/관세", "공급망", "기술 경쟁"]
        keywords = [
            ["캐즘", "EV", "보조금"],
            ["수요", "ESS", "PHEV", "HEV"],
            ["정책", "관세", "규제"],
            ["공급망", "원자재", "물류"],
            ["기술", "LFP", "전고체", "혁신"],
        ]

        text = analysis_text.lower()
        scores = []
        for group in keywords:
            score = sum(text.count(k.lower()) for k in group)
            scores.append(max(score, 1))

        fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
        bars = ax.bar(labels, scores, color=["#E4002B", "#F07A00", "#C00020", "#E8420A", "#F5A623"])
        ax.set_title("시장 외부환경 토픽 커버리지")
        ax.set_ylabel("언급 빈도 (상대)")
        ax.grid(axis="y", alpha=0.3)

        for b, s in zip(bars, scores):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), str(s), ha="center", va="bottom", fontsize=9)

        plt.tight_layout()
        self._save_figure(fig, "01_market_topic_coverage.png")

    def _generate_priority_radar_like_chart(self, analysis_text: str) -> None:
        labels = ["시장", "정책", "공급망", "기술", "리스크"]
        text = analysis_text.lower()
        raw_scores = [
            text.count("시장") + text.count("수요"),
            text.count("정책") + text.count("관세") + text.count("규제"),
            text.count("공급") + text.count("원자재") + text.count("물류"),
            text.count("기술") + text.count("전고체") + text.count("lfp"),
            text.count("리스크") + text.count("위험") + text.count("도전"),
        ]

        max_raw = max(raw_scores) if raw_scores else 1
        values = [max(1.0, (v / max_raw) * 10) for v in raw_scores]

        fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
        ax.plot(labels, values, marker="o", linewidth=2, color="#E4002B")
        ax.fill(labels, values, alpha=0.2, color="#F07A00")
        ax.set_ylim(0, 10)
        ax.set_title("시장조사 우선순위 프로파일")
        ax.grid(alpha=0.3)

        plt.tight_layout()
        self._save_figure(fig, "02_market_priority_profile.png")

    def _save_figure(self, fig, filename: str) -> None:
        path = self.output_dir / filename
        fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        self.generated_files.append(str(path.resolve()))
