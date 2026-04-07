# 🚀 프로젝트 구현 가이드 - 팀 협업 매뉴얼

## 📊 생성된 프로젝트 통계

```
총 Python 파일: 46개
전체 파일: 50개 (py, md, txt, example 등)

구성 모듈별 분포:
├─ agents/          : 18개 파일 (5개 Agent + base + supervisor)
├─ config/          : 3개  파일 (settings, schema, __init__)
├─ state/           : 2개  파일 (state_manager, __init__)
├─ retrieval/       : 2개  파일 (retriever, __init__)
├─ validators/      : 3개  파일 (base_validator, content_validators, __init__)
├─ workflows/       : 2개  파일 (retry_handler, __init__)
├─ report/          : 3개  파일 (markdown_builder, pdf_converter, __init__)
├─ shared/          : 4개  파일 (logger, utils, constants, __init__)
├─ scripts/         : 3개  파일 (run_workflow, demo_single_agent, __init__)
├─ tests/           : 3개  파일 (test_market_agent, test_validators, __init__)
├─ visualization/   : 1개  파일 (__init__ with ChartGenerator)
└─ 루트 파일       : 4개  파일 (README.md, requirements.txt, .env.example, .gitignore)
```

---

## 👥 팀 역할 분담 및 담당 모듈

### **Team A - Team Lead (Supervisor + Workflow)**
**책임**: 전체 시스템 조율 및 워크플로우 오케스트레이션

**주요 파일**:
- `agents/supervisor/agent.py` - Supervisor Agent 구현
- `agents/base.py` - BaseAgent 인터페이스 정의
- `workflows/retry_handler.py` - 재시도 로직
- `state/state_manager.py` - 상태 관리

**할 일**:
1. Supervisor Agent 완성 (현재 뼈대 완료 ✓)
2. State handoff 로직 검증 및 개선
3. 재시도 메커니즘 테스트
4. 전체 워크플로우 통합 테스트

**일정**: 1주차

---

### **Team B - 시장조사 + RAG**
**책임**: 시장 정보 수집 및 RAG 시스템 구축

**주요 파일**:
- `agents/market_research/agent.py` - 시장조사 Agent
- `agents/market_research/schema.py` - 출력 스키마
- `agents/market_research/prompts.py` - 프롬프트 템플릿
- `retrieval/retriever.py` - 문서 검색 엔진

**할 일**:
1. RAG 시스템 구축 (Chroma 또는 Pinecone)
2. 문서 로더 및 Chunker 구현
3. 임베딩 모델 연결 (OpenAI embeddings)
4. 시장조사 Agent의 LLM 프롬프트 최적화
5. 검색 결과 검증

**일정**: 1-2주차
**산출물**: `data/vector_store/` 채워짐, 시장조사 결과 (~2 페이지)

---

### **Team C - 기업조사 + State 관리**
**책임**: LG/CATL 기업 분석 및 State 스키마 관리

**주요 파일**:
- `agents/company_research/agent.py` - 기업조사 Agent
- `agents/company_research/schema.py` - CompanyProfile 스키마
- `agents/company_research/prompts.py` - 프롬프트 템플릿
- `state/models.py` - ProjectState 확장 (필요시)
- `config/schema.py` - 중앙 스키마

**할 일**:
1. CompanyProfile 데이터 모델 확장 (필요시)
2. LG 전략 분석 에이전트 최적화
3. CATL 전략 분석 에이전트 최적화
4. 에이전트 간 State 전달 검증
5. 기업 데이터 정확성 검증

**일정**: 2주차
**산출물**: LG 분석 (~1 페이지) + CATL 분석 (~1 페이지)

---

### **Team D - SWOT 분석 + 품질 검증**
**책임**: SWOT 분석 및 결과 품질 검증

**주요 파일**:
- `agents/swot_analysis/agent.py` - SWOT 분석 Agent
- `agents/swot_analysis/schema.py` - SWOTMatrix 스키마
- `agents/swot_analysis/prompts.py` - 프롬프트 템플릿
- `validators/content_validators.py` - SWOTValidator 구현
- `validators/base_validator.py` - 검증 기본 인터페이스

**할 일**:
1. SWOT 분석 에이전트 LLM 프롬프트 최적화
2. SWOTValidator 구현 및 검증 로직 추가
3. 비교분석 로직 구현
4. 실패 시 에이전트 재실행 트리거 테스트
5. 품질 기준 정의 및 검증 규칙 설정

**일정**: 2주차
**산출물**: SWOT 분석 (~2 페이지) + 비교분석

---

### **Team E - 보고서 작성 + Export**
**책임**: 최종 보고서 생성 및 구조화된 JSON 출력

**주요 파일**:
- `agents/report_writer/agent.py` - 보고서 작성 Agent
- `agents/report_writer/schema.py` - ReportOutput 스키마
- `agents/report_writer/prompts.py` - 프롬프트 템플릿
- `report/json_builder.py` - JSON 보고서 생성 (PRIMARY)
- `report/markdown_builder.py` - MD 보고서 생성 (OPTIONAL)
- `visualization/__init__.py` - 차트/다이어그램 생성

**할 일**:
1. 보고서 작성 Agent 최적화 (JSON 구조 기반)
2. 보고서 섹션별 구조화된 데이터 생성
3. JSON 출력 포맷 검증 및 최적화
4. Markdown 템플릿 개선
5. 시각화 모듈 완성 (SWOT 다이어그램 등)

**일정**: 3주차
**산출물**: battery_strategy_report_*.json (PRIMARY) + battery_strategy_report_*.md (OPTIONAL)

---

### **Team F - DevOps / CI-CD / QA**
**책임**: 설정 관리, 자동화, 테스트

**주요 파일**:
- `config/settings.py` - 전역 설정
- `config/schema.py` - 공유 스키마
- `shared/logger.py` - 로깅 설정
- `shared/constants.py` - 상수 정의
- `scripts/run_workflow.py` - 메인 실행 스크립트
- `scripts/demo_single_agent.py` - 개별 테스트 스크립트
- `.env.example` - 환경변수 템플릿
- `requirements.txt` - 의존성
- `tests/` - 전체 테스트 파일

**할 일**:
1. 의존성 설정 및 requirements.txt 검증
2. 환경변수 설정 자동화
3. 로깅 시스템 구축 및 테스트
4. 각 팀의 유닛 테스트 통합
5. CI/CD 파이프라인 구축 (GitHub Actions 등)
6. 문서화 완성 (README, docstring 등)
7. 성능 측정 및 최적화

**일정**: 1-3주차 지속
**산출물**: 자동화 스크립트 + 테스트 커버리지 70% 이상

---

## 🔄 워크플로우 및 팀 간 의존성

```
Week 1:
├─ Team A: Supervisor 기본 구현 + 워크플로우 구조
├─ Team B: RAG 시스템 준비 + 시장조사 Agent 기본 구현
├─ Team F: 환경 설정, 로깅, 기본 테스트 프레임워크
│
Week 2:
├─ Team B: 시장조사 Agent 완성 + 검증
├─ Team C: 기업조사 Agent 구현 + State handoff 테스트
├─ Team D: SWOT Agent 구현 + Validator 구현
├─ Team A: 워크플로우 통합 테스트 + 개선
├─ Team F: 통합 테스트
│
Week 3:
├─ Team E: 보고서 작성 Agent + 다중 포맷 변환
├─ Team F: 전체 시스템 테스트 + 성능 최적화
├─ 모든 팀: 최종 통합 테스트 + 문서화
└─ 최종 배포
```

---

## 📋 초기 셋업 (모든 팀이 함께)

### 1단계: 개발 환경 준비
```bash
# 저장소 클론
cd /Users/minhee/Documents/skala/ch21_Agent/Battery_analysis

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일 편집: OpenAI API 키 등 입력
```

### 2단계: 프로젝트 구조 이해
- `README.md` 숙독
- 각 팀의 담당 폴더 구조 파악
- `config/schema.py`의 ProjectState 이해

### 3단계: 개별 기능 테스트
```bash
# 개별 Agent 테스트
python scripts/demo_single_agent.py --agent market
python scripts/demo_single_agent.py --agent company
python scripts/demo_single_agent.py --agent swot
python scripts/demo_single_agent.py --agent report

# 테스트 실행
python -m pytest tests/
```

---

## 🔗 팀 간 협업 방식

### **State 기반 통신**
- 모든 Agent는 `ProjectState` 객체를 통해 데이터 전달
- Supervisor가 각 에이전트의 출력을 State에 저장
- 다음 에이전트는 State의 이전 결과를 참조

### **프롬프트 관리**
- 모든 LLM 프롬프트는 각 Agent의 `prompts.py`에 집중화
- 프롬프트 수정 시 해당 팀에서만 처리
- 프롬프트 버전 관리: `config/settings.py`에서 관리

### **스키마 정의**
- 각 Agent의 출력 스키마는 `agents/*/schema.py` 정의
- Schema 변경 시 Team A에 사전 공지
- 검증 로직은 `validators/content_validators.py`에서 관리

### **Git 협업 규칙**
```bash
# Branch 명명: team_[name]_[feature]
git checkout -b team_b_market_research

# Commit 메시지
git commit -m "[Team B] Implement market research agent"

# PR 전에 항상 테스트
python -m pytest tests/
```

---

## ✅ 품질 확인 체크리스트

### 각 팀이 완료 전에 확인할 사항

#### **Team B (시장조사)**
- [ ] RAG 검색 결과 5개 이상 반환
- [ ] 시장조사 결과 500자 이상, 5000자 이하
- [ ] 최소 10개 문장 이상
- [ ] 시장 규모, 성장률, 기술 트렌드 포함

#### **Team C (기업조사)**
- [ ] LG 분석 결과 500자 이상, 5000자 이하
- [ ] CATL 분석 결과 500자 이상, 5000자 이하
- [ ] 각 회사별 최소 10개 문장 이상
- [ ] 전략, 강점, 시장 위치 포함

#### **Team D (SWOT)**
- [ ] SWOT 키워드 (강점, 약점, 기회, 위협) 모두 포함
- [ ] LG/CATL 각각 최소 2개 항목씩
- [ ] 비교분석 최소 10개 문장
- [ ] 전략적 통찰력 포함

#### **Team E (보고서)**
- [ ] Markdown 파일 2000자 이상
- [ ] PDF 1.5MB 이하
- [ ] 목차, 각 섹션 명확
- [ ] 참고자료 리스트 포함

---

## 📞 문제 해결 및 소통

### 이슈 발생 시
1. `outputs/logs/`에서 에러 로그 확인
2. 해당 팀 리드에 Slack 공지
3. `tests/`에서 관련 테스트 실행
4. 필요시 팀 간 미팅 개최

### 정기 미팅
- **일일**: 아침 10분 스탠드업 (진행 상황 공유)
- **주중**: 수요일 30분 (이슈 해결)
- **주말**: 금요일 1시간 (전체 통합 테스트)

---

## 🎯 최종 성과물

### 완성 시 제공 물품
```
outputs/
├── reports_json/                                    # PRIMARY OUTPUT
│   └── battery_strategy_report_20240407_120000.json (구조화된 JSON)
├── reports_md/
│   └── battery_strategy_report_20240407_120000.md   (마크다운 형식)
├── logs/
│   └── battery_analysis_20240407.log                (모든 실행 기록)
└── state_history/                                   (상태 변화 이력)
    └── state_*.json
```

### JSON 보고서 구조
```json
{
  "metadata": {
    "title": "AI Agent 기반 배터리 시장 전략 보고서",
    "generated_at": "2024-04-07T12:00:00",
    "format": "json",
    "execution_id": "exec_20240407_120000_xxxxxxxx"
  },
  "executive_summary": "...",
  "sections": {
    "market_overview": { "title": "시장 개요", "content": "..." },
    "company_analysis": {
      "lg_energy_solution": { "title": "LG에너지솔루션", "content": "..." },
      "catl": { "title": "CATL", "content": "..." }
    },
    "swot_analysis": { "title": "SWOT 비교분석", "content": "..." },
    "conclusion": { "title": "결론 및 제안", "content": "..." }
  },
  "references": [],
  "workflow_status": { ... }
}
```

---

## 🚀 다음 단계

1. **현재**: 구조 완성 ✓
2. **1주차**: 각 팀이 담당 모듈 구현 시작
3. **2주차**: 통합 테스트 및 개선
4. **3주차**: 최종 polonization 및 배포
5. **4주차**: 모니터링 및 개선

---

**문서 작성**: 2024년 4월 7일
**담당**: 프로젝트 아키텍트
**마지막 업데이트**: 구조 완성 후
