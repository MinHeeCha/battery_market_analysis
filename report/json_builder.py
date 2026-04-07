"""
JSON report builder - outputs structured report as JSON
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from config.schema import ProjectState
from shared.logger import get_logger

logger = get_logger(__name__)


class JSONBuilder:
    """Builds JSON format reports from agent outputs"""
    
    def __init__(self, output_dir: str = "./outputs/reports_json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build_from_state(self, state: ProjectState) -> Dict[str, Any]:
        """Build structured JSON report from state"""
        logger.info("Building JSON report from state...")
        
        report = {
            "metadata": {
                "title": "AI Agent 기반 배터리 시장 전략 보고서",
                "generated_at": datetime.now().isoformat(),
                "execution_id": state.execution_id,
                "format": "json",
                "version": "1.0"
            },
            "executive_summary": "본 보고서는 배터리 시장의 현황을 분석하고 LG에너지솔루션과 CATL의 경쟁 전략을 비교 분석한 결과물입니다.",
            "sections": {
                "market_overview": {
                    "title": "시장 개요",
                    "content": state.market_background or "(시장 조사 결과 대기중)"
                },
                "company_analysis": {
                    "title": "기업 전략 분석",
                    "lg_energy_solution": {
                        "title": "LG에너지솔루션",
                        "content": state.lg_strategy or "(기업 조사 결과 대기중)"
                    },
                    "catl": {
                        "title": "CATL",
                        "content": state.catl_strategy or "(기업 조사 결과 대기중)"
                    }
                },
                "swot_analysis": {
                    "title": "SWOT 비교 분석",
                    "content": state.comparative_swot or "(SWOT 분석 결과 대기중)"
                },
                "conclusion": {
                    "title": "결론 및 제안",
                    "content": "본 분석을 통해 배터리 시장에서 경쟁하는 두 기업의 전략적 포지셔닝과 경쟁력을 파악할 수 있습니다. 각 기업의 강점을 살리고 약점을 보완하는 차별화된 전략이 필요합니다."
                }
            },
            "workflow_status": {
                "phases": {
                    "market_research": state.validation_status.get("market_research", False),
                    "company_research": state.validation_status.get("company_research", False),
                    "swot_analysis": state.validation_status.get("swot_analysis", False),
                    "report_writing": state.validation_status.get("report_writing", False)
                },
                "retry_counts": state.retry_count,
                "errors": state.errors
            }
        }
        
        return report
    
    def build_from_report_output(self, report_output: Dict[str, Any]) -> Dict[str, Any]:
        """Build JSON report from structured report output"""
        logger.info("Building JSON report from report output...")
        
        report = {
            "metadata": {
                "title": "AI Agent 기반 배터리 시장 전략 보고서",
                "generated_at": datetime.now().isoformat(),
                "format": "json",
                "version": "1.0"
            },
            "executive_summary": report_output.get("executive_summary", ""),
            "sections": {
                "market_overview": {
                    "title": "시장 개요",
                    "content": report_output.get("introduction", "")
                },
                "company_analysis": {
                    "title": "기업 전략 분석",
                    "lg_energy_solution": {
                        "title": "LG에너지솔루션",
                        "content": report_output.get("lg_analysis", "")
                    },
                    "catl": {
                        "title": "CATL",
                        "content": report_output.get("catl_analysis", "")
                    }
                },
                "swot_analysis": {
                    "title": "SWOT 비교 분석",
                    "content": report_output.get("comparative_swot", "")
                },
                "conclusion": {
                    "title": "결론 및 제안",
                    "content": report_output.get("conclusion_and_recommendation", "")
                }
            },
            "references": report_output.get("references", []),
            "report_metadata": report_output.get("metadata", {})
        }
        
        return report
    
    def save_report(self, report_data: Dict[str, Any], filename: Optional[str] = None, indent: int = 2) -> Path:
        """
        Save JSON report to file
        
        Args:
            report_data: Dictionary to save as JSON
            filename: Output filename (auto-generated if None)
            indent: JSON indentation level (2 or 4 recommended)
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"battery_strategy_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=indent, ensure_ascii=False, default=str)
        
        logger.info(f"JSON report saved to {filepath}")
        return filepath
    
    def load_report(self, filepath: Path) -> Dict[str, Any]:
        """Load JSON report from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON report loaded from {filepath}")
        return data
