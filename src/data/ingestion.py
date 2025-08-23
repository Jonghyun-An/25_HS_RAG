"""
Data Ingestion Module
데이터 수집 및 처리 모듈
"""

import os
from typing import List, Dict
from ..utils.config import get_config

def create_records_from_chunks(chunks: List[str]) -> List[Dict]:
    """청크들을 Pinecone 레코드 형태로 변환합니다."""
    records = []
    
    for i, chunk in enumerate(chunks):
        record = {
            "id": f"chunk_{i}",
            "content": chunk,
            "metadata": {
                "source": "보험약관",
                "chunk_index": i,
                "chunk_size": len(chunk)
            }
        }
        records.append(record)
    
    return records

def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF 파일에서 텍스트를 추출합니다."""
    text = ""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"PDF 파일 읽기 오류: {e}")
        return ""
    
    return text

def clean_text(text: str) -> str:
    """텍스트를 정리합니다."""
    import re
    # 불필요한 공백 제거
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    text = text.strip()
    
    return text

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """텍스트를 청킹합니다."""
    import re
    
    chunks = []
    text = clean_text(text)
    
    # 문장 단위로 분할
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    current_chunk = ""
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        if current_size + sentence_size > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            
            # 오버랩을 위해 마지막 부분을 유지
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + " " + sentence
            current_size = len(current_chunk)
        else:
            current_chunk += " " + sentence
            current_size += sentence_size
    
    # 마지막 청크 추가
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return [chunk for chunk in chunks if chunk.strip()]

def process_pdf_for_rag(pdf_path: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
    """PDF 파일을 RAG를 위해 처리합니다."""
    config = get_config()
    if chunk_size is None:
        chunk_size = config["chunk_size"]
    if chunk_overlap is None:
        chunk_overlap = config["chunk_overlap"]
    
    print(f"PDF 파일 처리 중: {pdf_path}")
    
    # 텍스트 추출
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("텍스트 추출 실패")
        return []
    
    print(f"추출된 텍스트 길이: {len(text)} 문자")
    
    # 청킹
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    print(f"생성된 청크 수: {len(chunks)}")
    
    return chunks

def ingest_pdf_to_pinecone(pdf_path: str, index_name: str = None):
    """PDF 파일을 처리하여 Pinecone용 레코드로 변환합니다."""
    config = get_config()
    if index_name is None:
        index_name = config["pinecone_index_name"]
    
    print(f"PDF 파일 처리 시작: {pdf_path}")
    
    # PDF에서 청크 추출
    chunks = process_pdf_for_rag(pdf_path)
    
    if not chunks:
        print("청크 추출 실패")
        return []
    
    print(f"총 {len(chunks)} 개의 청크가 생성되었습니다.")
    
    # 레코드 형태로 변환
    records = create_records_from_chunks(chunks)
    
    print(f"Pinecone 인덱스에 {len(records)}개 레코드 업로드를 시작합니다...")
    
    return records
