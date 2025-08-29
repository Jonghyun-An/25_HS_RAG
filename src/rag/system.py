import os
from typing import List, Dict, Any
from pinecone import Pinecone
import openai

# LangChain 관련 import
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.callbacks.manager import trace_as_chain_group

from ..utils.config import get_config, DEBUG_MODE, setup_langsmith

class InsuranceRAGSystem:
    """보험 약관 RAG 시스템"""
    
    def __init__(self):
        # LangSmith 설정 초기화
        self.langsmith_enabled = setup_langsmith()
        
        # 설정 로드
        self.config = get_config()
        
        # Pinecone 초기화
        self.pc = Pinecone(api_key=self.config["pinecone_api_key"])
        
        # 인덱스 연결
        index_name = self.config["pinecone_index_name"]
        index_description = self.pc.describe_index(index_name)
        self.index = self.pc.Index(host=index_description.host)
        
        # LangChain 모델 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=500,
            api_key=self.config["openai_api_key"]
        )
        
        # LangChain 프롬프트 템플릿
        self.prompt_template = ChatPromptTemplate.from_template("""
당신은 전문적인 보험 상담사입니다. 
제공된 LIG손해보험 약관 내용을 바탕으로 정확하고 도움이 되는 답변을 제공해주세요.

답변 지침:
1. 제공된 참고자료의 내용을 바탕으로만 답변하세요
2. 답변은 한국어로 명확하고 이해하기 쉽게 작성하세요  
3. 구체적인 조항이나 절차가 있다면 정확히 인용하세요
4. 만약 제공된 자료에서 정확한 답변을 찾을 수 없다면, 그 점을 명시하고 보험회사에 직접 문의하도록 안내하세요
5. 답변은 3-4문장으로 간결하게 작성하세요

다음 LIG손해보험 약관 내용을 참고하여 질문에 답변해주세요:

{context}

질문: {question}

답변:""")
        
        # LangChain 체인 구성
        self.rag_chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | self.prompt_template
            | self.llm
            | StrOutputParser()
        )
        
        print("✅ RAG 시스템이 초기화되었습니다.")
        if self.langsmith_enabled:
            print("🔍 LangSmith 추적이 활성화되었습니다.")
    
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
    
    def generate_answer_with_langchain(self, query: str, contexts: List[Dict], max_context_length: int = None) -> str:
        """
        LangChain을 사용하여 검색된 컨텍스트를 바탕으로 답변을 생성합니다.
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

            # LangChain 체인 실행 (환경 변수로 LangSmith 추적)
            answer = self.rag_chain.invoke({
                "context": context_text,
                "question": query
            })
            
            return answer.strip()
            
        except Exception as e:
            print(f"LangChain 답변 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            
            # LangChain 실패 시 폴백 답변
            if contexts:
                first_context = contexts[0].get('content', '')[:500]
                return f"검색된 약관 내용에 따르면: {first_context}... 더 구체적인 정보는 보험회사에 직접 문의해주세요."
            
            return "현재 답변을 생성할 수 없습니다. 보험회사에 직접 문의해주세요."
    
    def generate_answer(self, query: str, contexts: List[Dict], max_context_length: int = None) -> str:
        """
        기존 OpenAI API를 사용한 답변 생성 (하위 호환성 유지)
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
            response = openai.OpenAI(api_key=self.config["openai_api_key"]).chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API 호출 오류: {e}")
            
            # OpenAI API 실패 시 폴백 답변
            if contexts:
                first_context = contexts[0].get('content', '')[:500]
                return f"검색된 약관 내용에 따르면: {first_context}... 더 구체적인 정보는 보험회사에 직접 문의해주세요."
            
            return "현재 답변을 생성할 수 없습니다. 보험회사에 직접 문의해주세요."
    
    def ask(self, query: str, use_langchain: bool = True) -> Dict[str, Any]:
        """
        질문에 대한 답변을 반환합니다.
        """
        if DEBUG_MODE:
            print(f"🔍 질문: {query}")
            print(f"🔗 LangChain 사용: {use_langchain}")
        
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
        
        # 2. 답변 생성 (LangChain 또는 OpenAI API 선택)
        if use_langchain and self.langsmith_enabled:
            answer = self.generate_answer_with_langchain(query, relevant_chunks)
        else:
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
            'query': query,
            'langchain_used': use_langchain and self.langsmith_enabled
        }
