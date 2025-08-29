"""
Configuration Management
설정 관리 모듈
"""

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(override=True)

# 디버그 모드 설정
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

def get_config():
    """애플리케이션 설정을 반환합니다."""
    return {
        # OpenAI 설정
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        
        # Pinecone 설정
        "pinecone_api_key": os.getenv("PINECONE_API_KEY"),
        "pinecone_index_name": os.getenv("PINECONE_INDEX_NAME", "insurance-terms-rag"),
        
        # LangSmith 설정
        "langsmith_api_key": os.getenv("LANGSMITH_API_KEY"),
        "langsmith_project": os.getenv("LANGSMITH_PROJECT", "insurance-rag-system"),
        "langsmith_endpoint": os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
        "langsmith_tracing_v2": os.getenv("LANGSMITH_TRACING_V2", "true").lower() == "true",
        
        # 디버그 설정
        "debug_mode": DEBUG_MODE,
        
        # 검색 설정
        "max_search_results": int(os.getenv("MAX_SEARCH_RESULTS", "5")),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "multilingual-e5-large"),
        
        # 답변 생성 설정
        "max_context_length": int(os.getenv("MAX_CONTEXT_LENGTH", "3000")),
        "chunk_size": int(os.getenv("CHUNK_SIZE", "1000")),
        "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "200")),
    }

def validate_config():
    """필수 설정이 있는지 확인합니다."""
    config = get_config()
    required_keys = ["openai_api_key", "pinecone_api_key"]
    
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_keys)}")
    
    return True

def setup_langsmith():
    """LangSmith 설정을 초기화합니다."""
    config = get_config()
    
    if config.get("langsmith_api_key"):
        os.environ["LANGCHAIN_API_KEY"] = config["langsmith_api_key"]
        os.environ["LANGCHAIN_PROJECT"] = config["langsmith_project"]
        os.environ["LANGCHAIN_ENDPOINT"] = config["langsmith_endpoint"]
        os.environ["LANGCHAIN_TRACING_V2"] = str(config["langsmith_tracing_v2"])
        
        print(f"✅ LangSmith 설정 완료: 프로젝트 '{config['langsmith_project']}'")
        return True
    else:
        print("⚠️ LangSmith API 키가 설정되지 않았습니다. LangSmith 추적이 비활성화됩니다.")
        return False
