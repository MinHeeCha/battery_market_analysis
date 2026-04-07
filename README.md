# AI Agent 기반 배터리 시장 전략 보고서 시스템

> Supervisor Pattern을 활용한 멀티 에이전트 시스템

## 📋 개요

본 시스템은 배터리 시장과 주요 기업(LG에너지솔루션, CATL)을 자동으로 분석하여 전략 보고서를 생성하는 AI 에이전트 기반 시스템입니다.

### 핵심 특징
- **Supervisor Pattern**: 중앙 조율 에이전트가 전체 워크플로우 관리
- **모듈식 아키텍처**: 각 에이전트는 독립적으로 개발/테스트 가능
- **상태 기반 Handoff**: 모든 에이전트 간 데이터는 중앙 상태 객체를 통해 전달
- **품질 검증**: 각 단계별 자동 검증 프로세스
- **다중 출력 형식**: Markdown + PDF 보고서 자동 생성

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────┐
│        Supervisor Agent (조율)               │
├─────────────────────────────────────────────┤
│ ├─ Market Research Agent     (시장조사)     │
│ ├─ Company Research Agent    (기업조사)     │
│ ├─ SWOT Analysis Agent       (SWOT분석)    │
│ └─ Report Writer Agent       (보고서작성)   │
├─────────────────────────────────────────────┤
│ 지원 모듈                                    │
│ ├─ Retrieval (RAG)          (문서 검색)    │
│ ├─ Validators               (품질 검증)    │
│ ├─ StateManager             (상태 관리)    │
│ └─ ReportBuilder            (보고서 생성)  │
└─────────────────────────────────────────────┘
```

## 📁 프로젝트 구조

```
Battery_analysis/
├── agents/                     # 에이전트 구현체
│   ├── base.py                # 공통 인터페이스 (BaseAgent)
│   ├── supervisor/            # 조율 에이전트
│   ├── market_research/       # 시장조사 에이전트
│   ├── company_research/      # 기업조사 에이전트
│   ├── swot_analysis/         # SWOT 분석 에이전트
│   └── report_writer/         # 보고서 작성 에이전트
├── state/                     # 상태 관리
│   ├── state_manager.py       # 상태 지속성 관리
│   └── models.py              # 상태 데이터 모델
├── config/                    # 전역 설정
│   ├── settings.py            # 환경설정
│   └── schema.py              # 공유 스키마
├── retrieval/                 # RAG (Retrieval-Augmented Generation)
│   └── retriever.py           # 문서 검색 엔진
├── validators/                # 품질 검증
│   ├── base_validator.py      # 공통 검증 인터페이스
│   └── content_validators.py  # 각 에이전트별 검증
├── workflows/                 # 오케스트레이션
│   ├── retry_handler.py       # 재시도 로직 (exponential backoff)
│   └── handoff_manager.py     # 상태 handoff 관리
├── report/                    # 보고서 생성
│   ├── markdown_builder.py    # MD 보고서 생성
│   ├── pdf_converter.py       # PDF 변환
│   └── templates/             # 템플릿
├── visualization/             # 시각화
│   └── __init__.py            # SWOT 다이어그램, 차트 등
├── shared/                    # 공유 유틸리티
│   ├── utils.py               # 헬퍼 함수
│   ├── logger.py              # 로깅 설정
│   └── constants.py           # 상수 정의
├── scripts/                   # 실행 스크립트
│   ├── run_workflow.py        # 메인 워크플로우 실행
│   └── demo_single_agent.py   # 개별 에이전트 테스트
├── tests/                     # 테스트
│   ├── test_market_agent.py
│   ├── test_validators.py
│   └── ...
├── data/                      # 데이터 저장소
│   ├── raw/                   # 원본 문서
│   ├── processed/             # 처리된 데이터
│   └── vector_store/          # 벡터 DB
├── outputs/                   # 최종 산출물
│   ├── reports_json/          # JSON 보고서 (PRIMARY)
│   ├── reports_md/            # Markdown 보고서
│   └── logs/                  # 실행 로그
├── .env.example               # 환경변수 템플릿
├── requirements.txt           # Python 의존성
└── README.md                  # 이 파일
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론/디렉토리 진입
cd Battery_analysis

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는 venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일 수정 (LLM API 키 등)
```

### 2. 문서 준비 (선택사항)

```bash
# 분석용 문서/데이터를 data/raw/에 배치
# RAG 기능을 활용하려면 배터리 시장/기업 관련 문서 추가

# PDF 임베딩 및 벡터DB 구축
python scripts/ingest_documents.py --reset
```

### 3. 워크플로우 실행

```bash
# 전체 파이프라인 실행
python scripts/run_workflow.py

# 또는 개별 에이전트 테스트
python scripts/demo_single_agent.py --agent market
python scripts/demo_single_agent.py --agent company
python scripts/demo_single_agent.py --agent swot
python scripts/demo_single_agent.py --agent report
```

### 4. 출력물 확인

```
outputs/
├── reports_json/                          # PRIMARY OUTPUT
│   └── battery_strategy_report_YYYYMMDD_HHMMSS.json
├── reports_md/
│   └── battery_strategy_report_YYYYMMDD_HHMMSS.md
└── logs/
    └── battery_analysis_YYYYMMDD.log
```
```

## 👥 팀 역할 분담

| 팀원 | 역할 | 담당 모듈 | 일정 |
|-----|------|---------|------|
| **Team Lead (A)** | Supervisor + Workflow | `agents/supervisor/`, `workflows/` | 1주차 |
| **Team B** | 시장조사 + RAG | `agents/market_research/`, `retrieval/` | 1-2주차 |
| **Team C** | 기업조사 + State | `agents/company_research/`, `state/` | 2주차 |
| **Team D** | SWOT + 검증 | `agents/swot_analysis/`, `validators/` | 2주차 |
| **Team E** | 보고서 + Export | `agents/report_writer/`, `report/` | 3주차 |
| **Team F** | 설정 + CI/CD | `config/`, `scripts/`, `tests/` | 1-3주차 |

## 🔄 워크플로우 흐름

```
1. 초기화
   └─ ProjectState 생성, 실행 ID 할당

2. 시장조사
   ├─ Market Research Agent 실행
   ├─ RAG 검색 + LLM 분석
   └─ State.market_background 저장

3. 기업조사
   ├─ Company Research Agent 실행
   ├─ LG + CATL 분석
   └─ State.lg_strategy, catl_strategy 저장

4. SWOT 분석
   ├─ SWOT Analysis Agent 실행
   ├─ 비교 분석
   └─ State.comparative_swot 저장

5. 품질 검증
   ├─ 각 단계 출력 검증
   └─ 실패 시 해당 Agent 재실행 (retry_handler)

6. 보고서 작성
   ├─ Report Writer Agent 실행
   ├─ 모든 State 정보 통합
   └─ State.final_report 저장

7. 보고서 변환
   ├─ Markdown 생성 (markdown_builder.py)
   ├─ PDF 변환 (pdf_converter.py)
   └─ 참고자료 정리

8. Export
   └─ outputs/에 MD + PDF 저장
```

## 📊 Agent 별 책임

### Market Research Agent
- **입력**: 검색 쿼리, 시장 데이터
- **프로세스**: RAG 검색 → LLM 분석
- **출력**: 시장 규모, 성장률, 기술 트렌드, 경쟁구도 (~2 페이지)

### Company Research Agent
- **입력**: 기업명 (LG, CATL)
- **프로세스**: 기업별 검색 → LLM 전략 분석
- **출력**: LG 전략 (~1 페이지) + CATL 전략 (~1 페이지)

### SWOT Analysis Agent
- **입력**: market_background, lg_strategy, catl_strategy
- **프로세스**: 시장/기업 정보 종합 → SWOT 분석
- **출력**: LG SWOT + CATL SWOT + 비교분석 (~2 페이지)

### Report Writer Agent
- **입력**: 모든 State 정보 (market, lg, catl, swot)
- **프로세스**: 정보 통합 → 구성 및 작성
- **출력**: 최종 보고서 콘텐츠

## ⚙️ 설정 (config/)

### settings.py
```python
# LLM 설정
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-...

# RAG 설정
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_STORE_TYPE=chroma

# 실행 설정
MAX_RETRIES=3
LOG_LEVEL=INFO
```

### schema.py
`ProjectState` - 모든 에이전트가 참조하는 중앙 상태 객체
- `market_background`: 시장조사 결과
- `lg_strategy`: LG 분석 결과
- `catl_strategy`: CATL 분석 결과
- `comparative_swot`: SWOT 분석 결과
- `final_report`: 최종 보고서

## 🧪 테스트

```bash
# 전체 테스트 실행
python -m pytest tests/

# 특정 테스트만 실행
python -m pytest tests/test_market_agent.py
python -m pytest tests/test_validators.py

# 테스트 커버리지
python -m pytest --cov=. tests/
```

## 🔧 개발 가이드

### Agent 추가
1. `agents/[new_agent]/` 디렉토리 생성
2. `agent.py` - Agent 클래스 구현 (BaseAgent 상속)
3. `schema.py` - Output 스키마 정의
4. `prompts.py` - LLM 프롬프트 정의
5. `tests/test_[new_agent].py` - 테스트 작성
6. `agents/supervisor/agent.py`에 등록

### Validator 추가
1. `validators/content_validators.py`에 클래스 추가
2. `validate()` 메서드 구현
3. 필요한 검증 로직 추가

## 📝 로그

모든 실행 로그는 `outputs/logs/`에 저장됩니다.

```bash
# 로그 확인
tail -f outputs/logs/battery_analysis_*.log
```

## 🐛 문제 해결

### 1. LLM API 연결 오류
- `.env` 파일에서 `OPENAI_API_KEY` 확인
- API 키 유효성 및 쿼터 확인

### 2. RAG 검색 결과 없음
- `data/raw/`에 문서 배치 확인
- 벡터 DB 초기화 필요 시: `python scripts/ingest_documents.py`

### 3. 상태 저장 오류
- `outputs/` 디렉토리 권한 확인
- 디스크 공간 확인

## 📚 의존성

주요 패키지:
- `langchain` - LLM 통합
- `openai` - GPT API
- `pydantic` - 데이터 검증
- `pypandoc` - MD → PDF 변환
- `pytest` - 테스트 프레임워크

자세한 내용은 `requirements.txt` 참조

## 📄 라이선스

프로젝트 라이선스 정보 (자신의 라이선스로 수정)

## 👨‍💼 지원

문제 발생 시:
1. `outputs/logs/` 에서 에러 로그 확인
2. `tests/` 에서 관련 테스트 실행
3. 팀 슬랙/미팅에서 논의

---

**마지막 업데이트**: 2024년 4월
**시스템**: AI Agent 기반 배터리 시장 분석 보고서
