#!/usr/bin/env python3
"""
ReportWriterAgent 단독 테스트 스크립트

앞 단계 에이전트 결과를 모킹하여 보고서 생성 에이전트만 독립적으로 실행한다.
실행: python scripts/test_report_agent.py
"""
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.logger import get_logger
from agents.report_writer.agent import ReportWriterAgent
from report.json_builder import JSONBuilder
from report.markdown_builder import MarkdownBuilder
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


def run_test():
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

    report_data = result.get("result", {})

    # 3. JSON 보고서 저장
    json_builder = JSONBuilder(output_dir=f"{config.output_dir}/reports_json")
    json_report = json_builder.build_from_report_output(report_data)
    json_path = json_builder.save_report(json_report)
    logger.info(f"JSON 보고서 저장: {json_path}")

    # 4. Markdown 보고서 저장
    md_builder = MarkdownBuilder(output_dir=f"{config.output_dir}/reports_md")
    summary = report_data.get("summary", {})
    market = report_data.get("market_background", {})
    lges = report_data.get("lges_analysis", {})
    catl = report_data.get("catl_analysis", {})
    comparison = report_data.get("strategy_comparison", {})
    md_lines = [
        "# 배터리 시장 전략 비교 보고서 (테스트)\n",
        f"## 1. SUMMARY\n**핵심 결론:** {summary.get('key_conclusions', '')}\n\n"
        f"**시장 상황 요약:** {summary.get('market_summary', '')}\n\n"
        f"**기업별 전략 핵심:** {summary.get('company_strategy_summary', '')}\n\n"
        f"**비교 결과:** {summary.get('comparison_result', '')}\n\n"
        f"**인사이트 & 시사점:** {summary.get('insights', '')}",
        f"## 2. 시장 배경\n### 2.1 시장 규모 변화\n{market.get('market_size_trend', '')}\n\n"
        f"### 2.2 수요 변화\n{market.get('market_demand_change', '')}\n\n"
        f"### 2.3 정책 변화\n{market.get('policy_changes', '')}",
        f"## 3. LG에너지솔루션 전략 분석\n"
        f"**포트폴리오:** {lges.get('portfolio', '')}\n\n"
        f"**시장 대응:** {lges.get('market_response', '')}\n\n"
        f"**다각화:** {lges.get('diversification', '')}\n\n"
        f"**핵심 경쟁력:** {lges.get('core_competency', '')}\n\n"
        f"**수익성:** {lges.get('profitability', '')}\n\n"
        f"**리스크:** {lges.get('risks', '')}",
        f"## 4. CATL 전략 분석\n"
        f"**포트폴리오:** {catl.get('portfolio', '')}\n\n"
        f"**시장 대응:** {catl.get('market_response', '')}\n\n"
        f"**다각화:** {catl.get('diversification', '')}\n\n"
        f"**핵심 경쟁력:** {catl.get('core_competency', '')}\n\n"
        f"**수익성:** {catl.get('profitability', '')}\n\n"
        f"**리스크:** {catl.get('risks', '')}",
        f"## 5. 전략 비교 및 Comparative SWOT\n"
        f"**핵심 전략 비교:** {comparison.get('core_strategy_comparison', '')}\n\n"
        f"**LGES SWOT:** {comparison.get('lges_swot', '')}\n\n"
        f"**CATL SWOT:** {comparison.get('catl_swot', '')}\n\n"
        f"**Comparative SWOT:** {comparison.get('comparative_swot', '')}",
        f"## 6. 종합 시사점\n{report_data.get('overall_implications', '')}",
        "## 7. REFERENCE\n" + "\n".join(f"- {r}" for r in report_data.get("references", [])),
    ]
    md_path = md_builder.save_report("\n\n".join(md_lines))
    logger.info(f"Markdown 보고서 저장: {md_path}")

    # 5. 필수 필드 검증
    logger.info("\n--- 출력 필드 검증 ---")
    checks = [
        ("summary.key_conclusions",       summary.get("key_conclusions", "")),
        ("summary.market_summary",         summary.get("market_summary", "")),
        ("market_background.market_size_trend", market.get("market_size_trend", "")),
        ("lges_analysis.portfolio",        lges.get("portfolio", "")),
        ("catl_analysis.portfolio",        catl.get("portfolio", "")),
        ("strategy_comparison.comparative_swot", comparison.get("comparative_swot", "")),
        ("overall_implications",           report_data.get("overall_implications", "")),
    ]
    all_ok = True
    for field, value in checks:
        ok = bool(value and len(str(value)) > 10)
        status = "OK" if ok else "EMPTY"
        logger.info(f"  [{status}] {field}: {str(value)[:60]}...")
        if not ok:
            all_ok = False

    logger.info("=" * 55)
    if all_ok:
        logger.info("테스트 통과: 모든 필드가 정상 생성됨")
    else:
        logger.warning("테스트 경고: 일부 필드가 비어 있음 (LLM 연결 확인 필요)")
    logger.info("=" * 55)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(run_test())
