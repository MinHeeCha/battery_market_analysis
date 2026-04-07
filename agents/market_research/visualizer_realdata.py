"""
Market Research Visualizer
시장조사 결과를 시각화하여 보고서용 PNG 이미지 생성
- 시장조사 agent output 안의 실제 숫자만 사용
- 하드코딩된 예시 수치 사용 금지
- 가장 정보 전달력이 높은 2개의 차트만 생성
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib import rcParams

from shared.logger import get_logger

logger = get_logger(__name__)


class MarketVisualizerError(Exception):
    """Visualizer 관련 exception"""
    pass


class MarketResearchVisualizer:
    """시장조사 결과 시각화 생성기"""

    DEFAULT_OUTPUT_DIR = "./visualization"

    STYLE_CONFIG = {
        "figure_dpi": 300,
        "figure_size": (10, 6),
        "font_size": 11,
        "title_size": 14,
        "label_size": 12,
        "legend_size": 10,
        "color_palette": [
            "#1f77b4",  # blue
            "#ff7f0e",  # orange
            "#2ca02c",  # green
            "#d62728",  # red
            "#9467bd",  # purple
            "#8c564b",  # brown
        ],
    }

    REGION_KEYS = ["중국", "유럽", "북미", "미국", "한국", "일본", "기타", "글로벌"]
    MARKET_SIZE_UNITS = ["십억", "억", "조", "billion", "million", "trillion", "USD", "달러"]

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or self.DEFAULT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._setup_style()
        self.generated_files: List[str] = []

        logger.info(f"MarketResearchVisualizer initialized: {self.output_dir}")

    def _setup_style(self):
        """matplotlib 스타일 설정"""
        for font_name in ["AppleGothic", "Malgun Gothic", "DejaVu Sans"]:
            try:
                rcParams["font.family"] = font_name
                break
            except Exception:
                continue

        rcParams["figure.facecolor"] = "white"
        rcParams["axes.facecolor"] = "white"
        rcParams["font.size"] = self.STYLE_CONFIG["font_size"]
        rcParams["axes.grid"] = True
        rcParams["grid.alpha"] = 0.25
        rcParams["grid.linestyle"] = "--"
        rcParams["axes.unicode_minus"] = False

    def visualize_market_research(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        시장조사 결과를 기반으로 실제 숫자만 사용해 최대 2개의 차트 생성

        우선순위:
        1) 시장 규모/성장률
        2) 지역별 시장 비중

        숫자가 부족하면 생성 가능한 차트만 만든다.
        """
        self.generated_files = []
        analysis_text = analysis_result.get("final_answer", "")

        if not analysis_text.strip():
            raise MarketVisualizerError("analysis_result['final_answer'] is empty")

        logger.info("Starting visualization generation from real numeric data only...")

        extracted = self._extract_numeric_data_from_analysis(analysis_text)

        # 1순위: 시장 규모 / 성장률
        if extracted["market_size_series"] or extracted["growth_rate_series"]:
            logger.info("  → Generating chart 1: market size / growth")
            self._generate_market_size_and_growth_chart(extracted)
        else:
            logger.info("  → Skipped market size / growth chart: insufficient numeric data")

        # 2순위: 지역별 시장 비중
        if extracted["regional_share"]:
            logger.info("  → Generating chart 2: regional share")
            self._generate_regional_share_chart(extracted)
        else:
            logger.info("  → Skipped regional share chart: insufficient numeric data")

        if not self.generated_files:
            raise MarketVisualizerError(
                "No visualization was generated because no reliable numeric data "
                "could be extracted from the market agent output."
            )

        logger.info(f"✓ Generated {len(self.generated_files)} visualization files")
        return self.generated_files

    def _extract_numeric_data_from_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """
        final_answer 텍스트에서 실제 숫자만 추출
        """
        data = {
            "market_size_series": self._extract_market_size_series(analysis_text),
            "growth_rate_series": self._extract_growth_rate_series(analysis_text),
            "regional_share": self._extract_regional_share(analysis_text),
        }
        logger.debug(f"Extracted numeric data: {data}")
        return data

    def _extract_market_size_series(self, text: str) -> Optional[Dict[str, List[float]]]:
        """
        예시 인식:
        - 2023년 72억 달러
        - 2024년 시장 규모는 103 billion USD
        - 2025년 1.2조 달러
        """
        series: List[Tuple[int, float, str]] = []

        patterns = [
            r"(20\d{2})년[^.\n]{0,40}?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(조|억|십억)\s*(달러|원|USD)?",
            r"(20\d{2})년[^.\n]{0,40}?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(trillion|billion|million)\s*(USD|usd|dollars)?",
            r"(20\d{2})년[^.\n]{0,40}?시장\s*규모[^.\n]{0,20}?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(조|억|십억|trillion|billion|million)\s*(달러|USD)?",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                year = int(match.group(1))
                value = float(match.group(2).replace(",", ""))
                unit = match.group(3).lower()
                normalized = self._normalize_market_size_to_billion_usd(value, unit)
                if normalized is not None:
                    series.append((year, normalized, "십억 USD"))

        if len(series) < 2:
            return None

        # 연도별 중복 제거
        dedup: Dict[int, float] = {}
        for year, value, _ in series:
            dedup[year] = value

        years = sorted(dedup.keys())
        values = [dedup[y] for y in years]

        return {
            "years": years,
            "values": values,
            "unit": "십억 USD",
        }

    def _normalize_market_size_to_billion_usd(self, value: float, unit: str) -> Optional[float]:
        """
        모든 시장 규모를 '십억 USD' 기준으로 정규화
        """
        unit = unit.lower()

        if unit in ["십억", "billion"]:
            return value
        if unit in ["조", "trillion"]:
            return value * 1000.0
        if unit in ["억", "million"]:
            return value / 1000.0

        return None

    def _extract_growth_rate_series(self, text: str) -> Optional[Dict[str, List[float]]]:
        """
        예시 인식:
        - 2023년 20%
        - 2024년 성장률은 19.4%
        - 연도별 성장률은 2022년 20%, 2023년 19.4%, 2024년 18.5%
        """
        pairs: List[Tuple[int, float]] = []

        patterns = [
            r"(20\d{2})년[^.\n]{0,30}?(\d+(?:\.\d+)?)\s*%",
            r"(20\d{2})년[^.\n]{0,20}?성장률[^.\n]{0,15}?(\d+(?:\.\d+)?)\s*%",
            r"(20\d{2})[^.\n]{0,10}?[:：]?\s*(\d+(?:\.\d+)?)\s*%",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                year = int(match.group(1))
                value = float(match.group(2))
                if 0 <= value <= 100:
                    pairs.append((year, value))

        if len(pairs) < 2:
            return None

        dedup: Dict[int, float] = {}
        for year, value in pairs:
            dedup[year] = value

        years = sorted(dedup.keys())
        values = [dedup[y] for y in years]

        return {
            "years": years,
            "values": values,
            "unit": "%",
        }

    def _extract_regional_share(self, text: str) -> Optional[Dict[str, List[float]]]:
        """
        예시 인식:
        - 중국 시장이 35%, 유럽이 25%, 북미가 22%
        - 중국 35%, 유럽 25%, 북미 22%, 기타 18%
        """
        region_values: Dict[str, float] = {}

        region_patterns = [
            r"(중국|유럽|북미|미국|한국|일본|기타)[^\d%]{0,15}?(\d+(?:\.\d+)?)\s*%",
            r"(중국|유럽|북미|미국|한국|일본|기타)\s*(?:시장)?\s*(?:비중이|이|가|는)?\s*(\d+(?:\.\d+)?)\s*%",
        ]

        for pattern in region_patterns:
            for match in re.finditer(pattern, text):
                region = match.group(1)
                value = float(match.group(2))
                if 0 <= value <= 100:
                    region_values[region] = value

        if len(region_values) < 2:
            return None

        # 보고서용으로 자주 쓰는 순서 정렬
        ordered_regions = [r for r in ["중국", "유럽", "북미", "미국", "한국", "일본", "기타"] if r in region_values]
        values = [region_values[r] for r in ordered_regions]

        return {
            "regions": ordered_regions,
            "values": values,
            "unit": "%",
        }

    def _generate_market_size_and_growth_chart(self, extracted_data: Dict[str, Any]) -> Optional[str]:
        """
        차트 1:
        - 시장 규모와 성장률 중 실제 데이터가 있는 것만 그림
        - 둘 다 있으면 1x2 subplot
        - 하나만 있으면 단일 차트
        """
        try:
            market = extracted_data.get("market_size_series")
            growth = extracted_data.get("growth_rate_series")
            palette = self.STYLE_CONFIG["color_palette"]

            available_count = sum([market is not None, growth is not None])
            if available_count == 0:
                return None

            if available_count == 2:
                fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=self.STYLE_CONFIG["figure_dpi"])
                ax1, ax2 = axes
            else:
                fig, ax = plt.subplots(1, 1, figsize=(8, 6), dpi=self.STYLE_CONFIG["figure_dpi"])
                ax1 = ax2 = None
                if market is not None:
                    ax1 = ax
                else:
                    ax2 = ax

            if market is not None and ax1 is not None:
                years = market["years"]
                values = market["values"]

                ax1.plot(
                    years,
                    values,
                    marker="o",
                    linewidth=2.8,
                    markersize=8,
                    color=palette[0],
                )
                ax1.fill_between(years, values, alpha=0.18, color=palette[0])

                for x, y in zip(years, values):
                    ax1.text(x, y, f"{y:.1f}", ha="center", va="bottom", fontsize=9)

                ax1.set_title("글로벌 배터리 시장 규모 추이", fontsize=self.STYLE_CONFIG["title_size"], weight="bold")
                ax1.set_xlabel("연도", fontsize=self.STYLE_CONFIG["label_size"])
                ax1.set_ylabel(f"시장 규모 ({market['unit']})", fontsize=self.STYLE_CONFIG["label_size"])
                ax1.set_xticks(years)
                ax1.grid(True, alpha=0.25)

            if growth is not None and ax2 is not None:
                years = growth["years"]
                values = growth["values"]

                bars = ax2.bar(
                    years,
                    values,
                    color=palette[1],
                    alpha=0.85,
                    edgecolor="black",
                    linewidth=1.0,
                )

                for bar, val in zip(bars, values):
                    ax2.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height(),
                        f"{val:.1f}%",
                        ha="center",
                        va="bottom",
                        fontsize=9,
                        weight="bold",
                    )

                ax2.set_title("EV 배터리 시장 성장률", fontsize=self.STYLE_CONFIG["title_size"], weight="bold")
                ax2.set_xlabel("연도", fontsize=self.STYLE_CONFIG["label_size"])
                ax2.set_ylabel("성장률 (%)", fontsize=self.STYLE_CONFIG["label_size"])
                ax2.set_xticks(years)
                ax2.set_ylim(0, max(values) * 1.25)
                ax2.grid(True, alpha=0.25, axis="y")

            plt.tight_layout()
            return self._save_figure("01_market_size_and_growth.png")

        except Exception as e:
            logger.warning(f"Market size / growth chart generation failed: {e}")
            return None

    def _generate_regional_share_chart(self, extracted_data: Dict[str, Any]) -> Optional[str]:
        """
        차트 2:
        - 지역별 시장 비중
        """
        try:
            regional = extracted_data.get("regional_share")
            if regional is None:
                return None

            fig, ax = plt.subplots(1, 1, figsize=(8, 6), dpi=self.STYLE_CONFIG["figure_dpi"])
            palette = self.STYLE_CONFIG["color_palette"]

            regions = regional["regions"]
            values = regional["values"]

            bars = ax.bar(
                regions,
                values,
                color=palette[: len(regions)],
                alpha=0.85,
                edgecolor="black",
                linewidth=1.0,
            )

            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{val:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    weight="bold",
                )

            ax.set_title("지역별 시장 비중", fontsize=self.STYLE_CONFIG["title_size"], weight="bold")
            ax.set_xlabel("지역", fontsize=self.STYLE_CONFIG["label_size"])
            ax.set_ylabel("시장 비중 (%)", fontsize=self.STYLE_CONFIG["label_size"])
            ax.set_ylim(0, max(values) * 1.25)
            ax.grid(True, alpha=0.25, axis="y")

            plt.tight_layout()
            return self._save_figure("02_regional_market_share.png")

        except Exception as e:
            logger.warning(f"Regional share chart generation failed: {e}")
            return None

    def _save_figure(self, filename: str) -> str:
        filepath = self.output_dir / filename
        plt.savefig(
            filepath,
            dpi=self.STYLE_CONFIG["figure_dpi"],
            bbox_inches="tight",
            facecolor="white",
        )
        plt.close()

        absolute_path = str(filepath.absolute())
        self.generated_files.append(absolute_path)
        logger.info(f"Saved visualization: {filepath}")
        return absolute_path

    def get_generated_files(self) -> List[str]:
        return self.generated_files


# ============================================================================
# Standalone 사용 예시
# ============================================================================

def create_sample_market_research_output() -> Dict[str, Any]:
    return {
        "final_answer": """
        글로벌 배터리 시장 규모는 2022년 50 billion USD, 2023년 60 billion USD,
        2024년 72 billion USD로 확대되었다.
        EV 배터리 시장 성장률은 2022년 20%, 2023년 19.4%, 2024년 18.5%를 기록했다.
        중국 시장이 35%, 유럽이 25%, 북미가 22%, 기타 지역이 18%를 차지했다.
        """,
        "external_relevance_score": 95,
        "pass_evaluation": True,
        "evaluation_details": {},
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Market Research Visualizer Test")
    print("=" * 60)

    try:
        visualizer = MarketResearchVisualizer(output_dir="./visualization")
        sample_result = create_sample_market_research_output()

        print("\n시각화 생성 중...")
        generated_files = visualizer.visualize_market_research(sample_result)

        print(f"\n✓ 생성된 파일 수: {len(generated_files)}")
        for filepath in generated_files:
            print(f"  - {Path(filepath).name}")

        print("\n" + "=" * 60)
        print("저장 위치:")
        print(f"  {visualizer.output_dir.absolute()}")
        print("=" * 60)

    except MarketVisualizerError as e:
        print(f"\n✗ Visualization Error: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")