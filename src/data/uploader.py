"""
Pinecone Upload Module
Pinecone 업로드 모듈
"""

import os
from pinecone import Pinecone
from typing import List, Dict
from ..utils.config import get_config

def setup_pinecone():
    """Pinecone 클라이언트를 설정합니다."""
    config = get_config()
    api_key = config["pinecone_api_key"]
    
    if not api_key:
        raise ValueError("PINECONE_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    pc = Pinecone(api_key=api_key)
    return pc

def upload_to_pinecone(records: List[Dict], index_name: str = None, namespace: str = "default") -> bool:
    """레코드들을 Pinecone에 업로드합니다."""
    config = get_config()
    if index_name is None:
        index_name = config["pinecone_index_name"]
    
    try:
        pc = setup_pinecone()
        
        # 인덱스 연결
        index_description = pc.describe_index(index_name)
        index = pc.Index(host=index_description.host)
        
        print(f"인덱스 '{index_name}'에 연결되었습니다.")
        print(f"호스트: {index_description.host}")
        
        # 배치 단위로 업로드
        batch_size = 10
        total_records = len(records)
        
        for i in range(0, total_records, batch_size):
            batch = records[i:i+batch_size]
            
            # upsert_records를 위한 레코드 형태로 변환
            records_to_upsert = []
            for record in batch:
                record_data = {
                    "id": record["id"],  # _id 대신 id 사용
                    "text": record["content"],  # content를 text로 변경
                    "source": record["metadata"]["source"],
                    "chunk_index": record["metadata"]["chunk_index"],
                    "chunk_size": record["metadata"]["chunk_size"]
                }
                records_to_upsert.append(record_data)
            
            # field_mapping 제거하고 upsert_records 호출
            index.upsert_records(
                namespace=namespace,
                records=records_to_upsert
            )
            
            print(f"배치 {i//batch_size + 1}: {len(batch)}개 레코드 업로드 완료")
        
        return True
        
    except Exception as e:
        print(f"업로드 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_index_stats(index_name: str = None) -> Dict:
    """인덱스 통계를 반환합니다."""
    config = get_config()
    if index_name is None:
        index_name = config["pinecone_index_name"]
    
    try:
        pc = setup_pinecone()
        index_description = pc.describe_index(index_name)
        index = pc.Index(host=index_description.host)
        
        stats = index.describe_index_stats()
        return {
            "total_vector_count": stats.total_vector_count,
            "namespaces": list(stats.namespaces.keys()) if stats.namespaces else ["default"]
        }
    except Exception as e:
        print(f"통계 조회 중 오류 발생: {e}")
        return {"error": str(e)}
