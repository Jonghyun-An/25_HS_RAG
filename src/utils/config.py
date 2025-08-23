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
