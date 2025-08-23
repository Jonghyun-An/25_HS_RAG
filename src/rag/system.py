import os
from typing import List, Dict, Any
from pinecone import Pinecone
import openai

from ..utils.config import get_config, DEBUG_MODE

class InsuranceRAGSystem:
    """보험 약관 RAG 시스템"""
    
    def __init__(self):
        # 설정 로드
        self.config = get_config()
        
        # Pinecone 초기화
        self.pc = Pinecone(api_key=self.config["pinecone_api_key"])
        
        # 인덱스 연결
        index_name = self.config["pinecone_index_name"]
        index_description = self.pc.describe_index(index_name)
        self.index = self.pc.Index(host=index_description.host)
        
        # OpenAI 초기화
        self.client = openai.OpenAI(api_key=self.config["openai_api_key"])
        
        print("✅ RAG 시스템이 초기화되었습니다.")
    
    def search_relevant_chunks(self, query: str, top_k: int = 5, namespace: str = "default") -> List[Dict]:
        """
        쿼리와 관련된 청크를 검색합니다.
        """
        try:
            # Pinecone의 search_records 사용 (integrated inference)
            from pinecone import SearchQuery
            
            response = self.index.search_records(
                namespace=namespace,
                query=SearchQuery(
                    inputs={
                        "text": query,  # fieldMap의 "text" 필드 사용
                    },
                    top_k=top_k
                )
            )
            
            # 디버그 모드에서만 출력
            if DEBUG_MODE:
                print(f"검색 응답 타입: {type(response)}")
                print(f"응답 내용: {response}")
            
            # 결과 처리
            results = []
            
            # Pinecone 응답 구조에 맞게 수정
            if hasattr(response, 'result') and hasattr(response.result, 'hits'):
                hits = response.result.hits
                for hit in hits:
                    # fields 구조에서 데이터 추출
                    fields = hit.fields
                    result = {
                        'id': hit._id,
                        'score': hit._score,
                        'content': fields.get('text', ''),  # text 필드에서 내용 가져오기
                        'source': fields.get('source', '보험약관'),
                        'chunk_index': int(fields.get('chunk_index', 0)),
                        'chunk_size': int(fields.get('chunk_size', 0))
                    }
                    results.append(result)
            else:
                print("예상하지 못한 응답 구조입니다.")
                print(f"응답 객체 속성: {dir(response)}")
            
            if DEBUG_MODE:
                print(f"📄 {len(results)}개의 관련 문서를 찾았습니다.")
            return results
            
        except Exception as e:
            print(f"검색 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def generate_answer(self, query: str, contexts: List[Dict], max_context_length: int = None) -> str:
        """
        검색된 컨텍스트를 바탕으로 답변을 생성합니다.
        """
        if max_context_length is None:
            max_context_length = self.config["max_context_length"]
            
        try:
            # 컨텍스트 준비
            context_text = ""
            for i, ctx in enumerate(contexts[:3]):  # 상위 3개만 사용
                content = ctx.get('content', '')[:1000]  # 각 청크당 최대 1000자
                context_text += f"[참고자료 {i+1}]\n{content}\n\n"
            
            if len(context_text) > max_context_length:
                context_text = context_text[:max_context_length] + "..."
            
            if DEBUG_MODE:
                print(f"context_text: {context_text}")

            # 프롬프트 구성
            system_prompt = """당신은 전문적인 보험 상담사입니다. 
제공된 LIG손해보험 약관 내용을 바탕으로 정확하고 도움이 되는 답변을 제공해주세요.

답변 지침:
1. 제공된 참고자료의 내용을 바탕으로만 답변하세요
2. 답변은 한국어로 명확하고 이해하기 쉽게 작성하세요  
3. 구체적인 조항이나 절차가 있다면 정확히 인용하세요
4. 만약 제공된 자료에서 정확한 답변을 찾을 수 없다면, 그 점을 명시하고 보험회사에 직접 문의하도록 안내하세요
5. 답변은 3-4문장으로 간결하게 작성하세요"""

            user_prompt = f"""다음 LIG손해보험 약관 내용을 참고하여 질문에 답변해주세요:

{context_text}

질문: {query}

답변:"""
            
            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API 호출 오류: {e}")
            
            # OpenAI API 실패 시 폴백 답변
            if contexts:
                first_context = contexts[0].get('content', '')[:500]
                return f"검색된 약관 내용에 따르면: {first_context}... 더 구체적인 정보는 보험회사에 직접 문의해주세요."
            
            return "현재 답변을 생성할 수 없습니다. 보험회사에 직접 문의해주세요."
    
    def ask(self, query: str) -> Dict[str, Any]:
        """
        질문에 대한 답변을 반환합니다.
        """
        if DEBUG_MODE:
            print(f"🔍 질문: {query}")
        
        # 1. 관련 청크 검색
        relevant_chunks = self.search_relevant_chunks(query, top_k=self.config["max_search_results"])
        if DEBUG_MODE:
            print(f"📄 {len(relevant_chunks)}개의 관련 문서를 찾았습니다.")
        
        if not relevant_chunks:
            return {
                'answer': '죄송합니다. 관련된 보험 약관 내용을 찾을 수 없습니다.',
                'sources': [],
                'query': query
            }
        
        # 2. 답변 생성
        answer = self.generate_answer(query, relevant_chunks)
        
        # 3. 소스 정보 준비
        sources = []
        for chunk in relevant_chunks[:3]:
            sources.append({
                'id': chunk.get('id', ''),
                'score': chunk.get('score', 0.0),
                'content': chunk.get('content', ''),
                'source': chunk.get('source', '보험약관'),
                'chunk_index': chunk.get('chunk_index', 0),
                'chunk_size': chunk.get('chunk_size', 0)
            })
        
        return {
            'answer': answer,
            'sources': sources,
            'query': query
        }
