import streamlit as st
import requests
from src.settings import settings
import uuid

st.set_page_config(page_title="OnlineShopRAG Chat", page_icon="💬", layout="wide")

st.title("💬 OnlineShopRAG - Чат поддержки")

API_URL = st.sidebar.text_input("API URL", value=settings.api_url)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

with st.sidebar:
    st.header("Настройки")
    new_conversation = st.button("🆕 Новый диалог", use_container_width=True)
    if new_conversation:
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    if st.session_state.conversation_id:
        st.info(f"**Conversation ID:**\n`{st.session_state.conversation_id}`")
    
    st.divider()
    st.caption("Отправьте сообщение агенту поддержки")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Введите ваше сообщение..."):
    # Генерируем conversation_id только если его нет (при первом сообщении)
    if not st.session_state.conversation_id:
        st.session_state.conversation_id = str(uuid.uuid4())

    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Думаю..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "conversation_id": st.session_state.conversation_id,
                        "message": prompt,
                    },
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                
                answer = data.get("answer", "Ошибка: ответ не получен")
                chunks = data.get("chunks", [])
                
                st.markdown(answer)
                
                if chunks:
                    with st.expander(f"📄 Найдено {len(chunks)} релевантных чанков"):
                        for i, chunk in enumerate(chunks, 1):
                            st.markdown(f"**Чанк {i}** (score: {chunk.get('score', 0):.3f})")
                            st.text(chunk.get("text", "")[:200] + "...")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                })
            except requests.exceptions.RequestException as e:
                error_msg = f"Ошибка при обращении к API: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

