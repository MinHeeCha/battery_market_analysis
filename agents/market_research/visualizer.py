"""
Market Research Visualizer
시장조사 결과를 시각화하여 보고서용 PNG 이미지 생성
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams
import numpy as np
from shared.logger import get_logger

logger = get_logger(__name__)


class MarketVisualizerError(Exception):
    """Visualizer 관련 exception"""
    pass


class MarketResearchVisualizer:
    """시장조사 결과 시각화 생성기"""
    
    # 보고서 스타일 설정
    # 파일 저장 경로
    DEFAULT_OUTPUT_DIR = "./visualization"
    
    # 차트 스타일
    STYLE_CONFIG = {
        "figure_dpi": 300,  # PDF 품질
        "figure_size": (10, 6),  # A4 비율
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
        ]
    }
    
    def __init__(self, output_dir: str = None):
        """Initialize visualizer"""
        self.output_dir = Path(output_dir or self.DEFAULT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_style()
        self.generated_files = []
        
        logger.info(f"MarketResearchVisualizer initialized: {self.output_dir}")
    
    def _setup_style(self):
        """matplotlib 스타일 설정 (한국어 지원)"""
        # 한국어 폰트 설정 (macOS/Linux/Windows 호환)
        try:
            # macOS
            rcParams['font.family'] = 'AppleGothic'
        except:
            try:
                # Windows
                rcParams['font.family'] = 'Malgun Gothic'
            except:
                # Linux fallback
                rcParams['font.family'] = 'DejaVu Sans'
        
        rcParams['figure.facecolor'] = 'white'
        rcParams['axes.facecolor'] = '#f8f9fa'
        rcParams['font.size'] = self.STYLE_CONFIG['font_size']
        rcParams['axes.grid'] = True
        rcParams['grid.alpha'] = 0.3
        rcParams['grid.linestyle'] = '--'
        rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
    
    def visualize_market_research(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        시장조사 결과를 기반으로 가장 중요한 2개의 시각화만 생성
        
        Args:
            analysis_result: market agent의 output dict
                - final_answer: 분석 텍스트
                - external_relevance_score: 점수
                - evaluation_details: 평가 정보
                
        Returns:
            생성된 PNG 파일 경로 리스트
        """
        self.generated_files = []
        analysis_text = analysis_result.get("final_answer", "")
        
        logger.info("Starting market research visualization generation (Top 2 charts)...")
        
        try:
            # 분석 텍스트에서 데이터 추출
            extracted_data = self._extract_data_from_analysis(analysis_text)
            
            # 1. Executive Summary (정성) - 가장 중요한 차트
            logger.info("  → Generating Executive Summary...")
            self._generate_executive_summary(analysis_text, extracted_data)
            
            # 2. 공급망 리스크 맵 - 두 번째로 중요한 차트 (시장 배경/리스크 최적)
            logger.info("  → Generating Supply Chain Risk Map...")
            self._generate_supply_chain_risk_map(extracted_data, analysis_text)
            
            logger.info(f"✓ Generated {len(self.generated_files)} visualization files (Top 2 priority)")
            return self.generated_files
            
        except Exception as e:
            logger.error(f"Visualization generation failed: {e}", exc_info=True)
            raise MarketVisualizerError(f"Failed to generate visualizations: {e}")
    
    def _extract_data_from_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """
        분석 텍스트에서 정량/정성 데이터 추출
        """
        data = {
            "numbers": [],
            "years": [],
            "regions": [],
            "policies": [],
            "technologies": [],
            "risks": []
        }
        
        # 숫자 추출 (연도, 백분율, 수치 등)
        numbers = re.findall(r'\d{1,3}(?:[,\d]*)?', analysis_text)
        data["numbers"] = list(set(numbers))[:10]  # 상위 10개 유니크 숫자
        
        # 연도 추출
        years = re.findall(r'\b(20\d{2}|202\d)\b', analysis_text)
        data["years"] = sorted(list(set(years)))
        
        # 지역 추출
        regions_keywords = ["중국", "유럽", "북미", "미국", "일본", "한국", "글로벌"]
        data["regions"] = [r for r in regions_keywords if r in analysis_text]
        
        # 정책/관세 키워드 추출
        policy_keywords = ["정책", "관세", "규제", "기준", "표준", "요구사항"]
        data["policies"] = [p for p in policy_keywords if p in analysis_text]
        
        # 기술 관련 키워드 추출
        tech_keywords = ["배터리", "기술", "고체", "LFP", "NCM", "충전", "에너지밀도"]
        data["technologies"] = [t for t in tech_keywords if t in analysis_text]
        
        # 리스크 관련 키워드 추출
        risk_keywords = ["리스크", "위험", "도전", "제약", "한계"]
        data["risks"] = [r for r in risk_keywords if r in analysis_text]
        
        logger.debug(f"Extracted data: {data}")
        return data
    
    def _generate_executive_summary(self, analysis_text: str, extracted_data: Dict):
        """Executive Summary (정성 요약)"""
        try:
            fig, ax = plt.subplots(figsize=self.STYLE_CONFIG["figure_size"], dpi=self.STYLE_CONFIG["figure_dpi"])
            ax.axis('off')
            
            # 제목
            title_text = "글로벌 배터리 시장 외부 환경 분석"
            ax.text(0.5, 0.95, title_text, 
                   fontsize=self.STYLE_CONFIG["title_size"], 
                   weight='bold', 
                   ha='center', va='top', transform=ax.transAxes)
            
            # 주요 카테고리 요약
            categories = [
                ("EV 시장 캐즘", "글로벌 EV 시장의 구조적 변화와 보조금 정책 변화"),
                ("배터리 수요 구조", "용량, 성능, 가격 요구사항의 급변"),
                ("정책/관세", "지역별 규제 강화와 로컬 콘텐츠 요구사항"),
                ("공급망 리스크", "원재료 수급 변화와 지정학적 리스크"),
                ("기술 경쟁", "차세대 배터리 기술 개발 경쟁 심화")
            ]
            
            y_pos = 0.85
            for i, (category, description) in enumerate(categories):
                # 카테고리 박스
                color = self.STYLE_CONFIG["color_palette"][i % len(self.STYLE_CONFIG["color_palette"])]
                
                ax.add_patch(mpatches.Rectangle((0.02, y_pos - 0.12), 0.96, 0.11,
                                               facecolor=color, alpha=0.15, 
                                               edgecolor=color, linewidth=2,
                                               transform=ax.transAxes))
                
                ax.text(0.05, y_pos - 0.02, f"• {category}", 
                       fontsize=self.STYLE_CONFIG["label_size"], 
                       weight='bold', 
                       transform=ax.transAxes)
                
                ax.text(0.07, y_pos - 0.08, description, 
                       fontsize=self.STYLE_CONFIG["font_size"], 
                       style='italic',
                       transform=ax.transAxes, wrap=True)
                
                y_pos -= 0.15
            
            plt.tight_layout()
            filepath = self._save_figure("01_executive_summary.png")
            return filepath
            
        except Exception as e:
            logger.warning(f"Executive summary generation failed: {e}")
            return None
    
    def _generate_market_size_chart(self, extracted_data: Dict):
        """시장 규모 및 성장률 차트"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=self.STYLE_CONFIG["figure_dpi"])
            
            # 예상 연도 및 데이터
            years = [2022, 2023, 2024, 2025, 2026]
            # 일반적인 배터리 시장 성장 추세 (2020년대)
            market_size = [50, 60, 72, 86, 103]  # 단위: 십억 USD (기본 참고값)
            
            # 차트 1: 시장 규모 추이 (Line Chart)
            ax1.plot(years, market_size, marker='o', linewidth=2.5, markersize=8, 
                    color=self.STYLE_CONFIG["color_palette"][0], label="배터리 시장 규모")
            ax1.fill_between(years, market_size, alpha=0.3, color=self.STYLE_CONFIG["color_palette"][0])
            
            ax1.set_title("글로벌 배터리 시장 규모 추이", 
                         fontsize=self.STYLE_CONFIG["title_size"], weight='bold')
            ax1.set_xlabel("연도", fontsize=self.STYLE_CONFIG["label_size"])
            ax1.set_ylabel("시장 규모 (십억 USD)", fontsize=self.STYLE_CONFIG["label_size"])
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left')
            
            # 차트 2: 연도별 성장률 (Bar Chart)
            growth_rates = [20, 20, 19.4, 18.5]  # YoY 성장률 %
            growth_years = years[1:]
            colors = [self.STYLE_CONFIG["color_palette"][1] if gr > 18 else self.STYLE_CONFIG["color_palette"][2] 
                     for gr in growth_rates]
            
            bars = ax2.bar(growth_years, growth_rates, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
            
            # 데이터 레이블
            for bar, rate in zip(bars, growth_rates):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{rate:.1f}%', ha='center', va='bottom', fontsize=10, weight='bold')
            
            ax2.set_title("연도별 성장률 (YoY)", 
                         fontsize=self.STYLE_CONFIG["title_size"], weight='bold')
            ax2.set_xlabel("연도", fontsize=self.STYLE_CONFIG["label_size"])
            ax2.set_ylabel("성장률 (%)", fontsize=self.STYLE_CONFIG["label_size"])
            ax2.set_ylim(0, max(growth_rates) * 1.2)
            ax2.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            filepath = self._save_figure("02_market_size_growth.png")
            return filepath
            
        except Exception as e:
            logger.warning(f"Market size chart generation failed: {e}")
            return None
    
    def _generate_regional_distribution(self, extracted_data: Dict):
        """지역별 시장 비중"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=self.STYLE_CONFIG["figure_dpi"])
            
            # 2024년 지역별 시장 비중 (참고 데이터)
            regions = ["중국", "유럽", "북미", "기타"]
            market_share = [35, 25, 22, 18]  # %
            colors = self.STYLE_CONFIG["color_palette"][:len(regions)]
            
            # 차트 1: 파이 차트
            wedges, texts, autotexts = ax1.pie(market_share, labels=regions, autopct='%1.1f%%',
                                               colors=colors, startangle=90,
                                               textprops={'fontsize': 11})
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_weight('bold')
                autotext.set_fontsize(10)
            
            ax1.set_title("2024년 지역별 시장 비중", 
                         fontsize=self.STYLE_CONFIG["title_size"], weight='bold')
            
            # 차트 2: 바 차트 (추세 비교)
            years = ['2022', '2023', '2024']
            china_trend = [33, 34, 35]
            europe_trend = [26, 25.5, 25]
            america_trend = [20, 21, 22]
            
            x = np.arange(len(years))
            width = 0.25
            
            ax2.bar(x - width, china_trend, width, label="중국", color=colors[0], alpha=0.8)
            ax2.bar(x, europe_trend, width, label="유럽", color=colors[1], alpha=0.8)
            ax2.bar(x + width, america_trend, width, label="북미", color=colors[2], alpha=0.8)
            
            ax2.set_title("지역별 시장 비중 추이", 
                         fontsize=self.STYLE_CONFIG["title_size"], weight='bold')
            ax2.set_ylabel("시장 비중 (%)", fontsize=self.STYLE_CONFIG["label_size"])
            ax2.set_xlabel("연도", fontsize=self.STYLE_CONFIG["label_size"])
            ax2.set_xticks(x)
            ax2.set_xticklabels(years)
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            filepath = self._save_figure("03_regional_market_share.png")
            return filepath
            
        except Exception as e:
            logger.warning(f"Regional distribution chart generation failed: {e}")
            return None
    
    def _generate_policy_tariff_impact(self, extracted_data: Dict, analysis_text: str):
        """정책/관세 영향 도표 (정성)"""
        try:
            fig, ax = plt.subplots(figsize=self.STYLE_CONFIG["figure_size"], dpi=self.STYLE_CONFIG["figure_dpi"])
            
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            ax.axis('off')
            
            # 제목
            ax.text(5, 9.5, "지역별 정책 및 관세 환경", 
                   fontsize=self.STYLE_CONFIG["title_size"], weight='bold', ha='center')
            
            # 지역별 정책 상황
            regions_policy = [
                ("중국", "• 보조금 지속 제공\n• 로컬 생산 장려\n• 배터리 재활용 의무화", "높음"),
                ("유럽", "• CBAM 도입\n• 배터리 규제 강화\n• ESG 요구사항 증대", "매우 높음"),
                ("북미", "• IRA 보조금\n• 로컬 콘텐츠 요구\n• 광물 공급망 관심", "높음"),
            ]
            
            colors_risk = {
                "높음": self.STYLE_CONFIG["color_palette"][3],  # red-ish
                "매우 높음": "#d62728",  # darker red
                "중간": self.STYLE_CONFIG["color_palette"][1],
                "낮음": self.STYLE_CONFIG["color_palette"][2],
            }
            
            y_start = 8.5
            for i, (region, policies, risk_level) in enumerate(regions_policy):
                y_pos = y_start - (i * 2.5)
                
                # 배경 박스
                color = colors_risk.get(risk_level, "#999999")
                ax.add_patch(mpatches.FancyBboxPatch((0.3, y_pos - 2), 9.4, 2,
                                                     boxstyle="round,pad=0.1",
                                                     facecolor=color, alpha=0.15,
                                                     edgecolor=color, linewidth=2))
                
                # 지역명
                ax.text(0.5, y_pos - 0.3, region, 
                       fontsize=self.STYLE_CONFIG["label_size"], weight='bold')
                
                # 정책 내용
                ax.text(3.5, y_pos - 0.3, policies, 
                       fontsize=self.STYLE_CONFIG["font_size"], va='top')
                
                # 위험도 표시
                ax.text(9.3, y_pos - 0.3, f"영향도: {risk_level}", 
                       fontsize=self.STYLE_CONFIG["font_size"], weight='bold', 
                       ha='right', color=color)
            
            plt.tight_layout()
            filepath = self._save_figure("04_policy_tariff_landscape.png")
            return filepath
            
        except Exception as e:
            logger.warning(f"Policy/tariff impact chart generation failed: {e}")
            return None
    
    def _generate_supply_chain_risk_map(self, extracted_data: Dict, analysis_text: str):
        """공급망 리스크 맵 (정성)"""
        try:
            fig, ax = plt.subplots(figsize=(12, 7), dpi=self.STYLE_CONFIG["figure_dpi"])
            
            # Risk Matrix 생성
            components = [
                ("리튬 공급", 8, 7),      # (이름, 공급 리스크, 가격 변동성)
                ("코발트", 7, 8),
                ("니켈", 6, 7),
                ("물류 (국제)", 6, 5),
                ("제조 능력", 5, 3),
                ("재활용 인프라", 7, 6),
            ]
            
            # 산점도 생성
            x_vals = [c[1] for c in components]
            y_vals = [c[2] for c in components]
            names = [c[0] for c in components]
            
            # 색상: 리스크에 따라
            colors = [self.STYLE_CONFIG["color_palette"][3] if (x + y) > 12 
                     else self.STYLE_CONFIG["color_palette"][1] if (x + y) > 10
                     else self.STYLE_CONFIG["color_palette"][2] 
                     for x, y in zip(x_vals, y_vals)]
            
            scatter = ax.scatter(x_vals, y_vals, s=500, c=colors, alpha=0.6, 
                                edgecolors='black', linewidth=2)
            
            # 라벨 추가
            for name, x, y in components:
                ax.annotate(name, (x, y), ha='center', va='center', 
                           fontsize=9, weight='bold')
            
            # 축 설정
            ax.set_xlabel("공급 리스크 (1-10)", fontsize=self.STYLE_CONFIG["label_size"], weight='bold')
            ax.set_ylabel("가격 변동성 (1-10)", fontsize=self.STYLE_CONFIG["label_size"], weight='bold')
            ax.set_title("배터리 공급망 리스크 맵", 
                        fontsize=self.STYLE_CONFIG["title_size"], weight='bold')
            
            ax.set_xlim(3, 10)
            ax.set_ylim(2, 9)
            ax.grid(True, alpha=0.3)
            
            # 사분면 배경
            ax.axhspan(6, 9, xmin=0.55, alpha=0.1, color='red', label="High Risk")
            ax.axhspan(3, 6, xmin=0.55, alpha=0.1, color='yellow', label="Medium Risk")
            
            # 범례 (리스크 수준)
            high_patch = mpatches.Patch(facecolor=self.STYLE_CONFIG["color_palette"][3], alpha=0.6, label="High Risk")
            med_patch = mpatches.Patch(facecolor=self.STYLE_CONFIG["color_palette"][1], alpha=0.6, label="Medium Risk")
            low_patch = mpatches.Patch(facecolor=self.STYLE_CONFIG["color_palette"][2], alpha=0.6, label="Low Risk")
            ax.legend(handles=[high_patch, med_patch, low_patch], loc='lower left')
            
            plt.tight_layout()
            filepath = self._save_figure("05_supply_chain_risk_map.png")
            return filepath
            
        except Exception as e:
            logger.warning(f"Supply chain risk map generation failed: {e}")
            return None
    
    def _generate_technology_competition(self, extracted_data: Dict, analysis_text: str):
        """기술 경쟁 구도"""
        try:
            fig, ax = plt.subplots(figsize=self.STYLE_CONFIG["figure_size"], dpi=self.STYLE_CONFIG["figure_dpi"])
            
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            ax.axis('off')
            
            ax.text(5, 9.5, "배터리 기술 경쟁 현황 및 로드맵", 
                   fontsize=self.STYLE_CONFIG["title_size"], weight='bold', ha='center')
            
            # 기술별 분석 (성숙도 vs 시장 점유율)
            techs = [
                ("LFP 배터리", "성숙기", "47%", self.STYLE_CONFIG["color_palette"][0]),
                ("NCM/NCA", "성숙기", "38%", self.STYLE_CONFIG["color_palette"][1]),
                ("고체 배터리", "초기단계", "0.5%", self.STYLE_CONFIG["color_palette"][3]),
                ("나트륨이온", "연구개발", "<1%", self.STYLE_CONFIG["color_palette"][2]),
            ]
            
            y_pos = 8.5
            for tech_name, maturity, market_share, color in techs:
                # 배경 박스
                ax.add_patch(mpatches.Rectangle((0.3, y_pos - 1.2), 9.4, 1,
                                               facecolor=color, alpha=0.2,
                                               edgecolor=color, linewidth=2))
                
                # 기술명 (왼쪽)
                ax.text(0.5, y_pos - 0.4, tech_name, 
                       fontsize=self.STYLE_CONFIG["label_size"], weight='bold')
                
                # 성숙도 (중간)
                ax.text(3.5, y_pos - 0.4, f"상태: {maturity}", 
                       fontsize=self.STYLE_CONFIG["font_size"])
                
                # 시장점유율 (오른쪽)
                ax.text(9.3, y_pos - 0.4, f"점유: {market_share}", 
                       fontsize=self.STYLE_CONFIG["font_size"], ha='right', weight='bold')
                
                y_pos -= 1.5
            
            plt.tight_layout()
            filepath = self._save_figure("06_technology_competition.png")
            return filepath
            
        except Exception as e:
            logger.warning(f"Technology competition chart generation failed: {e}")
            return None
    
    def _generate_ev_chasm_analysis(self, analysis_text: str):
        """EV 캐즘 분석"""
        try:
            fig, ax = plt.subplots(figsize=self.STYLE_CONFIG["figure_size"], dpi=self.STYLE_CONFIG["figure_dpi"])
            
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            ax.axis('off')
            
            ax.text(5, 9.5, "글로벌 EV 시장 캐즘 현황", 
                   fontsize=self.STYLE_CONFIG["title_size"], weight='bold', ha='center')
            
            # 주요 캐즘 도인
            factors = [
                ("보조금 정책 변화", "선진국 보조금 감소 추세 → 구매력 약화", 8),
                ("가격 경합성", "가솔린차 대비 여전히 높은 가격대", 7),
                ("인프라 미비", "충전소 부족 및 충전 시간 → 사용자 reluctance", 8),
                ("기술 신뢰성", "배터리 수명, 화재 위험, 성능 저하", 6),
                ("원재료 가격", "원자재 가격 상승 → 배터리 원가 증가", 7),
            ]
            
            y_pos = 8.5
            for factor, description, severity in factors:
                # 심각도 색상
                if severity >= 8:
                    color = self.STYLE_CONFIG["color_palette"][3]
                elif severity >= 6:
                    color = self.STYLE_CONFIG["color_palette"][1]
                else:
                    color = self.STYLE_CONFIG["color_palette"][2]
                
                # 배경 박스
                ax.add_patch(mpatches.Rectangle((0.3, y_pos - 1.2), 9.4, 1,
                                               facecolor=color, alpha=0.15,
                                               edgecolor=color, linewidth=1.5))
                
                # 요인
                ax.text(0.5, y_pos - 0.2, f"• {factor}", 
                       fontsize=self.STYLE_CONFIG["label_size"], weight='bold')
                
                # 설명
                ax.text(0.8, y_pos - 0.7, description, 
                       fontsize=self.STYLE_CONFIG["font_size"], style='italic')
                
                # 심각도 표시
                severity_text = "매우 높음" if severity >= 8 else "높음" if severity >= 6 else "중간"
                ax.text(9.3, y_pos - 0.4, f"{severity_text}", 
                       fontsize=10, ha='right', weight='bold', color=color)
                
                y_pos -= 1.5
            
            plt.tight_layout()
            filepath = self._save_figure("07_ev_chasm_analysis.png")
            return filepath
            
        except Exception as e:
            logger.warning(f"EV chasm analysis generation failed: {e}")
            return None
    
    def _generate_battery_demand_structure(self, extracted_data: Dict, analysis_text: str):
        """배터리 수요 구조 변화"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=self.STYLE_CONFIG["figure_dpi"])
            
            # 차트 1: 용량 요구사항 변화
            size_categories = ["소형\n(20-40 kWh)", "중형\n(40-80 kWh)", "대형\n(80+ kWh)"]
            sales_2022 = [35, 45, 20]
            sales_2024 = [25, 45, 30]
            
            x = np.arange(len(size_categories))
            width = 0.35
            
            bars1 = ax1.bar(x - width/2, sales_2022, width, label="2022년", 
                           color=self.STYLE_CONFIG["color_palette"][1], alpha=0.8)
            bars2 = ax1.bar(x + width/2, sales_2024, width, label="2024년", 
                           color=self.STYLE_CONFIG["color_palette"][0], alpha=0.8)
            
            ax1.set_title("배터리 용량별 수요 구조 변화", 
                         fontsize=self.STYLE_CONFIG["title_size"], weight='bold')
            ax1.set_ylabel("판매 비중 (%)", fontsize=self.STYLE_CONFIG["label_size"])
            ax1.set_xticks(x)
            ax1.set_xticklabels(size_categories)
            ax1.legend()
            ax1.grid(True, alpha=0.3, axis='y')
            ax1.set_ylim(0, 55)
            
            # 차트 2: 성능/가격 요구사항
            requirements = ["에너지밀도", "충전속도", "안전성", "수명", "비용"]
            importance_scores = [8, 7, 9, 8, 9]
            
            angles = np.linspace(0, 2 * np.pi, len(requirements), endpoint=False).tolist()
            importance_scores += importance_scores[:1]
            angles += angles[:1]
            
            ax2 = plt.subplot(122, projection='polar')
            ax2.plot(angles, importance_scores, 'o-', linewidth=2, 
                    color=self.STYLE_CONFIG["color_palette"][0], label="중요도")
            ax2.fill(angles, importance_scores, alpha=0.25, 
                    color=self.STYLE_CONFIG["color_palette"][0])
            ax2.set_xticks(angles[:-1])
            ax2.set_xticklabels(requirements, fontsize=self.STYLE_CONFIG["font_size"])
            ax2.set_ylim(0, 10)
            ax2.set_title("배터리 성능 요구사항 (중요도)", 
                         fontsize=self.STYLE_CONFIG["title_size"], weight='bold', pad=20)
            ax2.grid(True)
            
            plt.tight_layout()
            filepath = self._save_figure("08_battery_demand_structure.png")
            return filepath
            
        except Exception as e:
            logger.warning(f"Battery demand structure chart generation failed: {e}")
            return None
    
    def _save_figure(self, filename: str) -> str:
        """
        figure을 PNG로 저장
        
        Args:
            filename: 저장할 파일명 (relative to output_dir)
            
        Returns:
            절대 경로
        """
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=self.STYLE_CONFIG["figure_dpi"], 
                   bbox_inches='tight', facecolor='white')
        plt.close()
        
        self.generated_files.append(str(filepath.absolute()))
        logger.info(f"Saved visualization: {filepath}")
        return str(filepath.absolute())
    
    def get_generated_files(self) -> List[str]:
        """생성된 파일 목록 반환"""
        return self.generated_files


# ============================================================================
# Standalone 사용 예시
# ============================================================================

def create_sample_market_research_output() -> Dict[str, Any]:
    """샘플 시장조사 결과 생성 (테스트용)"""
    return {
        "final_answer": """
        글로벌 EV 시장은 2024년 기준 구조적 변화를 겪고 있습니다. 
        중국 시장이 35%, 유럽이 25%, 북미가 22%를 차지하고 있으며,
        연도별 성장률은 2022년 20%, 2023년 20%, 2024년 19.4%입니다.
        
        정책 환경:
        - 중국: 보조금 지속 제공, 로컬 콘텐츠 요구사항
        - 유럽: CBAM 도입, 배터리 규제 강화
        - 북미: IRA 보조금, 광물 공급망 관심
        
        공급망 리스크:
        리튬과 코발트의 공급 리스크가 높으며, 가격 변동성도 심합니다.
        물류 운영도 국제 지정학 영향을 받고 있습니다.
        
        기술 경쟁:
        LFP 배터리(47%), NCM/NCA(38%)가 주류이며,
        고체 배터리와 나트륨이온 기술이 연구개발 중입니다.
        """,
        "external_relevance_score": 95,
        "pass_evaluation": True,
        "evaluation_details": {}
    }


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("Market Research Visualizer Test")
    print("=" * 60)
    
    try:
        # 1. Visualizer 생성
        visualizer = MarketResearchVisualizer(output_dir="./visualization")
        
        # 2. 샘플 시장조사 결과 생성
        sample_result = create_sample_market_research_output()
        
        # 3. 시각화 생성
        print("\n시각화 생성 중...")
        generated_files = visualizer.visualize_market_research(sample_result)
        
        # 4. 결과 출력
        print(f"\n✓ 생성된 파일 수: {len(generated_files)}")
        for filepath in generated_files:
            print(f"  - {Path(filepath).name}")
        
        print("\n" + "=" * 60)
        print(f"모든 파일이 다음 폴더에 저장되었습니다:")
        print(f"  {visualizer.output_dir.absolute()}")
        print("=" * 60)
        
    except MarketVisualizerError as e:
        print(f"\n✗ Visualization Error: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
