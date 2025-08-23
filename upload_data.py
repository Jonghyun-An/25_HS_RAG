#!/usr/bin/env python3
"""
Data Upload Script
데이터 업로드 스크립트

사용법:
    python upload_data.py [PDF_파일_경로]
    
예시:
    python upload_data.py ./docs/embeding_test_pdf.pdf
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data import ingest_pdf_to_pinecone, upload_to_pinecone
from src.utils.config import get_config, validate_config

def main():
    """메인 함수"""
    try:
        # 설정 검증
        validate_config()
        config = get_config()
        
        print("📚 보험 약관 데이터 업로드 시스템")
        print("=" * 50)
        
        # PDF 파일 경로 확인
        if len(sys.argv) > 1:
            pdf_path = sys.argv[1]
        else:
            pdf_path = "./docs/embeding_test_pdf.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
            print("\n사용법: python upload_data.py [PDF_파일_경로]")
            return False
        
        print(f"📄 처리할 PDF 파일: {pdf_path}")
        print(f"🎯 대상 인덱스: {config['pinecone_index_name']}")
        
        # PDF 데이터 처리
        records = ingest_pdf_to_pinecone(pdf_path)
        
        if not records:
            print("❌ 레코드 생성 실패")
            return False
        
        print(f"✅ {len(records)}개 레코드 생성 완료")
        
        # Pinecone에 업로드
        print("\n🚀 Pinecone 업로드 시작...")
        success = upload_to_pinecone(records)
        
        if success:
            print("\n🎉 모든 데이터가 성공적으로 업로드되었습니다!")
            
            # 업로드 결과 요약
            print("\n📊 업로드 요약:")
            print(f"  - 총 청크 수: {len(records)}")
            print(f"  - 인덱스 이름: {config['pinecone_index_name']}")
            print(f"  - 네임스페이스: default")
            
            return True
        else:
            print("\n💥 업로드 중 오류가 발생했습니다.")
            return False
            
    except Exception as e:
        print(f"\n💥 시스템 오류: {e}")
        if config.get("debug_mode", False):
            import traceback
            traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
