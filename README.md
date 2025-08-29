# 보험 약관 RAG 시스템

LIG손해보험 약관 기반의 질의응답 시스템입니다.
(Forked from https://github.com/cfcf26/sample_rag)

## 🆕 새로운 기능

### 🔍 LangSmith 연동
- **LangChain 추적**: 모든 RAG 과정을 LangSmith에서 실시간으로 모니터링
- **성능 분석**: 답변 생성 시간, 토큰 사용량, 검색 품질 등 상세 분석
- **A/B 테스트**: 다양한 프롬프트와 모델 설정 비교 가능
- **오류 추적**: 문제 발생 시 상세한 디버깅 정보 제공

## 📁 프로젝트 구조

```
sample_rag/
├── app.py                    # 🚀 메인 Streamlit 웹 애플리케이션
├── upload_data.py           # 📤 데이터 업로드 스크립트
├── src/                     # 📦 핵심 소스 코드
│   ├── rag/                 # 🧠 RAG 시스템
│   │   ├── __init__.py
│   │   └── system.py        # RAG 시스템 메인 클래스 (LangChain 통합)
│   ├── data/                # 📊 데이터 처리
│   │   ├── __init__.py
│   │   ├── ingestion.py     # PDF 데이터 수집 및 처리
│   │   └── uploader.py      # Pinecone 업로드
│   └── utils/               # 🛠️ 유틸리티
│       ├── __init__.py
│       └── config.py        # 설정 관리 (LangSmith 설정 포함)
├── docs/                    # 📄 문서 파일들
├── requirements.txt         # 📋 Python 의존성
├── pyproject.toml          # 🔧 프로젝트 설정
├── env.example             # 🌍 환경 변수 예시
└── README.md               # 📖 이 파일
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
uv install

# 환경 변수 설정 (.env 파일 생성 또는 직접 설정)
export OPENAI_API_KEY="your_openai_api_key"
export PINECONE_API_KEY="your_pinecone_api_key"
export PINECONE_INDEX_NAME="insurance-terms-rag"

# LangSmith 연동 (선택사항)
export LANGSMITH_API_KEY="your_langsmith_api_key"
export LANGSMITH_PROJECT="insurance-rag-system"
export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
export LANGSMITH_TRACING_V2="true"

export DEBUG_MODE="false"
```

### 2. 데이터 업로드

```bash
# PDF 파일을 Pinecone에 업로드
python upload_data.py ./docs/embeding_test_pdf.pdf

# 또는 uv 사용
uv run python upload_data.py ./docs/embeding_test_pdf.pdf
```

### 3. 웹 애플리케이션 실행

```bash
# Streamlit 앱 실행
streamlit run app.py

# 또는 uv 사용
uv run streamlit run app.py
```

## 🔧 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 | (필수) |
| `PINECONE_API_KEY` | Pinecone API 키 | (필수) |
| `PINECONE_INDEX_NAME` | Pinecone 인덱스 이름 | `insurance-terms-rag` |
| `LANGSMITH_API_KEY` | LangSmith API 키 | (선택) |
| `LANGSMITH_PROJECT` | LangSmith 프로젝트명 | `insurance-rag-system` |
| `LANGSMITH_ENDPOINT` | LangSmith API 엔드포인트 | `https://api.smith.langchain.com` |
| `LANGSMITH_TRACING_V2` | LangSmith V2 추적 활성화 | `true` |
| `DEBUG_MODE` | 디버그 모드 활성화 | `false` |
| `MAX_SEARCH_RESULTS` | 최대 검색 결과 수 | `5` |
| `MAX_CONTEXT_LENGTH` | 최대 컨텍스트 길이 | `3000` |
| `CHUNK_SIZE` | 청크 크기 | `1000` |
| `CHUNK_OVERLAP` | 청크 오버랩 | `200` |

## 🎯 주요 기능

### 📱 웹 인터페이스 (`app.py`)
- Streamlit 기반 사용자 친화적 인터페이스
- 실시간 질의응답
- 참고 자료 표시
- **LangSmith 연동 상태 표시**
- **LangChain 사용 여부 선택**
- 디버그 모드 지원

### 📤 데이터 업로드 (`upload_data.py`)
- PDF 파일 자동 처리
- 텍스트 청킹
- Pinecone 자동 업로드
- 배치 처리 지원

### 🧠 RAG 시스템 (`src/rag/system.py`)
- Pinecone 벡터 검색
- **LangChain 기반 답변 생성**
- **OpenAI API 직접 호출 (폴백)**
- 컨텍스트 기반 응답
- **LangSmith 추적 통합**

### 📊 데이터 처리 (`src/data/`)
- PDF 텍스트 추출
- 스마트 청킹 (문장 단위 분할)
- 메타데이터 관리

## 🔍 LangSmith 연동 가이드

### 1. LangSmith 계정 생성
1. [LangSmith](https://smith.langchain.com/)에 가입
2. API 키 생성
3. 새 프로젝트 생성 (예: `insurance-rag-system`)

### 2. 환경 변수 설정
```bash
export LANGSMITH_API_KEY="ls_..."
export LANGSMITH_PROJECT="insurance-rag-system"
```

### 3. 추적 확인
- 웹 앱 사이드바에서 "🔍 LangSmith 추적 활성화됨" 메시지 확인
- LangSmith 대시보드에서 실시간 추적 확인
- 각 질문-답변 쌍의 상세 분석 가능

### 4. 추적 데이터 활용
- **성능 모니터링**: 응답 시간, 토큰 사용량 추적
- **품질 개선**: 프롬프트 최적화, 모델 튜닝
- **오류 분석**: 실패한 요청의 상세 원인 파악
- **사용자 행동**: 질문 패턴, 답변 만족도 분석

## 🛠️ 개발자 가이드

### 모듈 사용 예시

```python
from src.rag import InsuranceRAGSystem
from src.data import ingest_pdf_to_pinecone, upload_to_pinecone
from src.utils.config import get_config

# RAG 시스템 초기화
rag = InsuranceRAGSystem()

# 질문하기
result = rag.ask("보험계약은 어떻게 성립되나요?")
print(result['answer'])

# 데이터 처리
records = ingest_pdf_to_pinecone("path/to/pdf")
upload_to_pinecone(records)
```

### 디버그 모드

```bash
# 디버그 모드로 실행
DEBUG_MODE=true uv run streamlit run app.py
```

디버그 모드에서는 다음 정보를 확인할 수 있습니다:
- 검색 결과 상세 정보
- Pinecone 인덱스 통계
- 시스템 상태
- 오류 스택 트레이스

## 🔍 문제 해결

### 일반적인 문제

1. **API 키 오류**: 환경 변수가 올바르게 설정되었는지 확인
2. **Pinecone 연결 오류**: 인덱스 이름과 API 키 확인
3. **PDF 처리 오류**: PDF 파일 경로와 읽기 권한 확인

### 로그 확인

디버그 모드를 활성화하여 상세한 로그를 확인할 수 있습니다:

```bash
DEBUG_MODE=true python upload_data.py your_file.pdf
```

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.
