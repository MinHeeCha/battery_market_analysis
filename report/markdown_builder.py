"""
Markdown report builder
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from config.schema import ProjectState
from shared.logger import get_logger

logger = get_logger(__name__)


class MarkdownBuilder:
    """Builds markdown reports from agent outputs"""
    
    def __init__(self, output_dir: str = "./outputs/reports_md"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build_from_state(self, state: ProjectState) -> str:
        """Build markdown report from state"""
        logger.info("Building markdown report...")
        
        report = f"""# AI Agent 기반 배터리 시장 전략 보고서

**생성 일시**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}  
**실행 ID**: {state.execution_id}

---

## Executive Summary

본 보고서는 AI Agent를 활용한 자동 분석 시스템으로 생성되었습니다.  
배터리 시장의 현황을 분석하고 LG에너지솔루션과 CATL의 경쟁 전략을 비교 분석했습니다.

---

## 1. 시장 개요

{state.market_background or '(시장 조사 결과 대기중)'}

---

## 2. 기업 전략 분석

### 2.1 LG에너지솔루션

{state.lg_strategy or '(기업 조사 결과 대기중)'}

### 2.2 CATL

{state.catl_strategy or '(기업 조사 결과 대기중)'}

---

## 3. SWOT 비교 분석

{state.comparative_swot or '(SWOT 분석 결과 대기중)'}

---

## 4. 결론 및 제안

본 분석을 통해 배터리 시장에서 경쟁하는 두 기업의 전략적 포지셔닝과 경쟁력을 파악할 수 있습니다.  
각 기업의 강점을 살리고 약점을 보완하는 차별화된 전략이 필요합니다.

---

## 참고사항

- 생성 방식: AI Agent 기반 자동 분석
- 분석 단계: 시장조사 → 기업조사 → SWOT분석 → 보고서작성
- 품질 검증: 각 단계별 검증 프로세스 적용

---

*이 보고서는 자동 생성되었습니다. 자세한 내용은 분석팀에 문의하시기 바랍니다.*
"""
        
        return report
    
    def save_report(self, content: str, filename: Optional[str] = None) -> Path:
        """Save markdown report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"battery_strategy_report_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Markdown report saved to {filepath}")
        return filepath
