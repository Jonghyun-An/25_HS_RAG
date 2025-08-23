import streamlit as st
import time
import os
from typing import Dict, Any
from src.rag import InsuranceRAGSystem
from src.utils.config import get_config, DEBUG_MODE

# 페이지 설정
st.set_page_config(
    page_title="보험 약관 챗봇",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사용자 정의 CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E5CFF;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px 15px;
        border-radius: 20px;
        margin: 5px 0;
        text-align: right;
    }
    
    .bot-message {
        background-color: #e9ecef;
        color: #333;
        padding: 10px 15px;
        border-radius: 20px;
        margin: 5px 0;
        text-align: left;
    }
    
    /* 다크모드에서 메시지 배경색 조정 */
    @media (prefers-color-scheme: dark) {
        .bot-message {
            background-color: #3b3b3b !important;
            color: #e0e0e0 !important;
        }
        
        .chat-container {
            background-color: #1e1e1e !important;
        }
    }
    
    .source-box {
        background-color: var(--background-color-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        font-size: 0.9rem;
        color: var(--text-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 다크모드/라이트모드 대응 */
    [data-theme="dark"] .source-box {
        background-color: #2b2b2b;
        border: 1px solid #404040;
        color: #e0e0e0;
    }
    
    [data-theme="light"] .source-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    
    /* Streamlit 기본 다크모드 감지 */
    @media (prefers-color-scheme: dark) {
        .source-box {
            background-color: #2b2b2b !important;
            border: 1px solid #404040 !important;
            color: #e0e0e0 !important;
        }
    }
    
    @media (prefers-color-scheme: light) {
        .source-box {
            background-color: #fff3cd !important;
            border: 1px solid #ffeaa7 !important;
            color: #856404 !important;
        }
    }
    
    .example-question {
        background-color: #e3f2fd;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 3px;
        cursor: pointer;
        border: 1px solid #bbdefb;
        display: inline-block;
    }
    
    .stats-box {
        background-color: #f1f3f4;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'rag_system' not in st.session_state:
    with st.spinner("🔧 RAG 시스템을 초기화하는 중..."):
        try:
            st.session_state.rag_system = InsuranceRAGSystem()
            st.success("✅ RAG 시스템이 성공적으로 초기화되었습니다!")
        except Exception as e:
            st.error(f"❌ RAG 시스템 초기화 실패: {e}")
            st.stop()

# 메인 헤더
st.markdown('<h1 class="main-header">🏠 LIG 보험 약관 챗봇</h1>', unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.header("📋 사용 가이드")
    st.markdown("""
    **보험 약관에 대해 궁금한 것을 물어보세요!**
    
    💡 **예시 질문들:**
    - 보험계약은 어떻게 성립되나요?
    - 보험료 납입이 연체되면 어떻게 되나요?
    - 청약을 철회할 수 있나요?
    - 보험금은 언제 지급되나요?
    - 계약을 해지하려면 어떻게 해야 하나요?
    """)
    
    st.header("📊 시스템 정보")
    st.info("🔍 Pinecone 벡터 검색\n🤖 multilingual-e5-large 임베딩\n📚 104개 보험약관 청크")
    
    if st.button("🗑️ 채팅 기록 지우기"):
        st.session_state.messages = []
        st.rerun()

# 메인 콘텐츠 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 채팅")
    
    # 채팅 기록 표시
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)
                
                # 소스 정보 표시
                if "sources" in message:
                    with st.expander("📚 참고 자료 보기", expanded=False):
                        for i, source in enumerate(message["sources"], 1):
                            st.markdown(f"""
                            <div class="source-box">
                                <strong style="color: #2E5CFF;">📄 참고자료 {i}</strong>
                                <span style="font-size: 0.8rem; opacity: 0.7;">(점수: {source['score']:.3f}, 청크: {source['chunk_index']})</span>
                                <hr style="margin: 8px 0; opacity: 0.3;">
                                <div style="line-height: 1.5;">{source['content']}</div>
                            </div>
                            """, unsafe_allow_html=True)

with col2:
    st.subheader("🎯 빠른 질문")
    
    # 예시 질문 버튼들
    example_questions = [
        "보험계약은 어떻게 성립되나요?",
        "보험료 납입이 연체되면 어떻게 되나요?",
        "청약을 철회할 수 있나요?",
        "보험금 지급 조건은 무엇인가요?",
        "계약 해지 절차를 알려주세요"
    ]
    
    for question in example_questions:
        if st.button(question, key=f"example_{hash(question)}"):
            # 예시 질문을 입력창에 설정
            st.session_state.example_question = question

# 채팅 입력
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "질문을 입력하세요...", 
        value=st.session_state.get('example_question', ''),
        key="user_input",
        placeholder="보험 약관에 대해 궁금한 것을 물어보세요!"
    )
    
    submit_button = st.form_submit_button("전송 📤")

# 예시 질문 처리
if 'example_question' in st.session_state:
    if st.session_state.example_question:
        user_input = st.session_state.example_question
        submit_button = True
        del st.session_state.example_question

# 디버그 모드 상태 확인 (환경 변수에서 읽기)
debug_mode = st.sidebar.checkbox("🐛 디버그 모드", value=DEBUG_MODE)

# 메시지 처리
if submit_button and user_input.strip():
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 답변 생성
    with st.spinner("🔍 보험 약관을 검색하고 답변을 생성하는 중..."):
        try:
            result = st.session_state.rag_system.ask(user_input)
            
            # 디버그 모드용 검색 결과 저장
            if debug_mode:
                st.session_state.last_search_results = result.get("sources", [])
                st.session_state.last_query = user_input
                st.session_state.last_answer_length = len(result["answer"])
            
            # 봇 메시지 추가
            bot_message = {
                "role": "assistant", 
                "content": result["answer"],
                "sources": result["sources"]
            }
            st.session_state.messages.append(bot_message)
            
            # 디버그 정보 출력 (메인 화면에)
            if debug_mode:
                st.success(f"✅ 답변 생성 완료: {len(result['sources'])}개 참고자료, {len(result['answer'])}자 답변")
            
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {e}")
            
            # 디버그 모드에서 상세 오류 정보 표시
            if debug_mode:
                import traceback
                st.error("상세 오류 정보:")
                st.code(traceback.format_exc())
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "죄송합니다. 시스템에 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            })
    
    st.rerun()

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    🏢 LIG손해보험 보험약관 챗봇 | 
    🔍 Pinecone Vector Database | 
    🤖 Streamlit RAG System
    <br><small>이 챗봇은 보험약관 정보를 제공하며, 정확한 상담은 보험회사에 직접 문의하세요.</small>
</div>
""", unsafe_allow_html=True)

# 디버그 정보 (개발 시에만 표시)

if debug_mode:
    st.sidebar.subheader("🔍 디버그 정보")
    
    # RAG 시스템 상세 정보
    with st.sidebar.expander("📊 RAG 시스템 상태", expanded=True):
        rag_info = {}
        
        # 기본 상태 정보
        rag_info["시스템_초기화"] = "정상" if 'rag_system' in st.session_state else "실패"
        rag_info["총_메시지_수"] = len(st.session_state.messages)
        
        # 최근 질문/답변 정보
        if st.session_state.messages:
            user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
            assistant_messages = [msg for msg in st.session_state.messages if msg["role"] == "assistant"]
            rag_info["사용자_질문_수"] = len(user_messages)
            rag_info["봇_응답_수"] = len(assistant_messages)
            
            if user_messages:
                rag_info["마지막_질문"] = user_messages[-1]["content"][:50] + "..."
        
        # 검색 관련 정보
        if hasattr(st.session_state, 'last_search_results'):
            rag_info["마지막_검색_결과_수"] = len(st.session_state.last_search_results)
            if st.session_state.last_search_results:
                avg_score = sum(r.get('score', 0) for r in st.session_state.last_search_results) / len(st.session_state.last_search_results)
                rag_info["평균_검색_점수"] = f"{avg_score:.3f}"
        
        # 답변 생성 정보
        if hasattr(st.session_state, 'last_answer_length'):
            rag_info["마지막_답변_길이"] = f"{st.session_state.last_answer_length}자"
        
        # 네임스페이스 정보 (Pinecone)
        if 'rag_system' in st.session_state:
            try:
                # Pinecone 인덱스 정보
                index_stats = st.session_state.rag_system.index.describe_index_stats()
                rag_info["총_벡터_수"] = index_stats.total_vector_count if hasattr(index_stats, 'total_vector_count') else "알 수 없음"
                
                # 네임스페이스 정보
                if hasattr(index_stats, 'namespaces') and index_stats.namespaces:
                    rag_info["사용_가능_네임스페이스"] = list(index_stats.namespaces.keys())
                    # 각 네임스페이스의 벡터 수
                    for ns_name, ns_info in index_stats.namespaces.items():
                        if hasattr(ns_info, 'vector_count'):
                            rag_info[f"네임스페이스_{ns_name}_벡터수"] = ns_info.vector_count
                else:
                    rag_info["네임스페이스"] = "default"
                    
                # 인덱스 차원 정보
                if hasattr(index_stats, 'dimension'):
                    rag_info["벡터_차원"] = index_stats.dimension
                    
            except Exception as e:
                rag_info["인덱스_상태"] = f"조회 실패: {str(e)[:50]}..."
                import traceback
                if debug_mode:
                    rag_info["인덱스_오류_상세"] = traceback.format_exc()[:200] + "..."
        
        st.sidebar.json(rag_info)
    
    # 마지막 검색 결과 표시
    if hasattr(st.session_state, 'last_search_results'):
        with st.sidebar.expander("🔍 마지막 검색 결과"):
            for i, result in enumerate(st.session_state.last_search_results, 1):
                with st.sidebar.expander(f"검색 결과 {i} (점수: {result.get('score', 0):.3f})"):
                    st.sidebar.write(f"**ID:** {result.get('id', 'N/A')}")
                    st.sidebar.write(f"**청크 인덱스:** {result.get('chunk_index', 'N/A')}")
                    st.sidebar.write(f"**소스:** {result.get('source', 'N/A')}")
                    st.sidebar.write(f"**내용 (처음 200자):** {result.get('content', '')[:200]}...")
    
    # 최근 대화 이력
    with st.sidebar.expander("💬 최근 대화 요약"):
        if st.session_state.messages:
            recent_messages = st.session_state.messages[-6:]  # 최근 6개만
            for i, msg in enumerate(recent_messages):
                role_icon = "👤" if msg["role"] == "user" else "🤖"
                content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                st.sidebar.write(f"{role_icon} {content_preview}")
                if msg["role"] == "assistant" and "sources" in msg:
                    st.sidebar.caption(f"참고자료: {len(msg['sources'])}개")
        else:
            st.sidebar.write("아직 대화가 없습니다.")
    
    # 필터링된 세션 상태 (UI 관련 제외)
    with st.sidebar.expander("🔧 기술적 세션 정보"):
        filtered_session = {
            key: str(value)[:100] + "..." if len(str(value)) > 100 else value
            for key, value in st.session_state.items()
            if not key.startswith(('example_', 'FormSubmitter:')) and 
               key not in ['rag_system', 'messages', 'user_input']
        }
        if filtered_session:
            st.sidebar.json(filtered_session)
        else:
            st.sidebar.write("표시할 기술적 정보가 없습니다.")
