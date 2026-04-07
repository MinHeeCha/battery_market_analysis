#!/usr/bin/env python3
"""
ReportWriterAgent 단독 테스트 스크립트

앞 단계 에이전트 결과를 모킹하여 보고서 생성 에이전트만 독립적으로 실행한다.
실행: python tests/test_report_agent.py
"""
import sys
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from shared.logger import get_logger
from agents.report_writer.agent import ReportWriterAgent
from utils.markdown_builder import MarkdownBuilder
from config.settings import config

logger = get_logger("test_report_agent")

# ── 앞 단계 에이전트 출력 모킹 ──────────────────────────────────────────────
MOCK_CONTEXT = {
    "execution_id": "test-report-001",
    "market_background": (
        "글로벌 배터리 시장은 2024년 기준 약 1,200억 달러 규모로, "
        "전기차 수요 급증과 에너지저장장치(ESS) 보급 확대에 힘입어 "
        "연평균 20% 이상 성장하고 있다. 주요 지역별로는 중국이 전체 생산량의 "
        "약 75%를 차지하며, 유럽과 북미는 현지 생산 확대를 추진 중이다."
    ),
    "lg_strategy": (
        "LG에너지솔루션은 파우치형 배터리 기술력을 바탕으로 북미·유럽 완성차 "
        "업체와의 합작법인(JV) 전략을 추진하고 있다. GM, Stellantis 등과 "
        "협력하여 현지 생산 역량을 강화하고, 고에너지밀도 셀 개발에 집중하고 있다. "
        "2025년까지 원통형 배터리 라인업을 확장해 Tesla 외 다변화를 노린다."
    ),
    "catl_strategy": (
        "CATL은 LFP(리튬인산철) 배터리의 원가 경쟁력을 앞세워 글로벌 점유율 "
        "약 37%를 유지하고 있다. 나트륨이온 배터리, 반고체 배터리 등 차세대 "
        "기술 개발에 대규모 투자를 진행 중이며, 헝가리 공장을 통해 유럽 공략을 "
        "강화하고 있다. 가격 경쟁력과 공급망 수직계열화가 핵심 강점이다."
    ),
    "comparative_swot": (
        "【LG에너지솔루션】\n"
        "강점: 고성능 파우치셀 기술, 글로벌 완성차 파트너십\n"
        "약점: 중국 대비 높은 원가 구조, LFP 라인업 부재\n"
        "기회: 북미 IRA 수혜, 프리미엄 EV 시장 성장\n"
        "위협: CATL의 가격 공세, 원자재 수급 불안정\n\n"
        "【CATL】\n"
        "강점: 압도적 원가 경쟁력, 대규모 생산 능력\n"
        "약점: 미·유럽 지정학적 리스크, 브랜드 인지도 부족\n"
        "기회: 신흥국 전기차 시장 확대, ESS 수요 급증\n"
        "위협: 서방국 보조금 차별, 한·일 업체의 추격"
    ),
}


def test_report_agent_output():
    logger.info("=" * 55)
    logger.info("ReportWriterAgent 단독 테스트 시작")
    logger.info("=" * 55)

    # 1. 에이전트 생성 및 실행
    agent = ReportWriterAgent()
    logger.info(f"LLM 연결 상태: {'사용 가능' if agent.llm else '미연결 (플레이스홀더 사용)'}")

    result = agent.run(MOCK_CONTEXT)

    # 2. 결과 출력
    logger.info("\n--- 에이전트 출력 (result) ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    report_markdown = result.get("result", "")

    # 3. Markdown 보고서 저장
    md_builder = MarkdownBuilder(output_dir=f"{config.output_dir}/reports_md")
    md_path = md_builder.save_report(report_markdown)
    logger.info(f"Markdown 보고서 저장: {md_path}")

    # 4. 필수 섹션 검증
    logger.info("\n--- 출력 섹션 검증 ---")
    checks = [
        ("title", "# 배터리 시장 전략 비교 보고서"),
        ("summary", "## 1. SUMMARY"),
        ("market", "## 2. 시장 배경"),
        ("lges", "## 3. LG에너지솔루션 전략 분석"),
        ("catl", "## 4. CATL 전략 분석"),
        ("swot", "## 5. 전략 비교 및 Comparative SWOT"),
        ("comparative_swot", "### 5.4 Comparative SWOT"),
        ("implications", "## 6. 종합 시사점"),
    ]
    all_ok = True
    for field, expected_text in checks:
        ok = expected_text in report_markdown
        status = "OK" if ok else "EMPTY"
        logger.info(f"  [{status}] {field}: {expected_text}")
        if not ok:
            all_ok = False

    logger.info("=" * 55)
    if all_ok:
        logger.info("테스트 통과: 모든 필드가 정상 생성됨")
    else:
        logger.warning("테스트 경고: 일부 필드가 비어 있음 (LLM 연결 확인 필요)")
    logger.info("=" * 55)

    assert all_ok, "Some required report fields were empty"


if __name__ == "__main__":
    try:
        test_report_agent_output()
    except pytest.skip.Exception:
        raise
    sys.exit(0)
