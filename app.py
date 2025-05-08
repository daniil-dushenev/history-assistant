import streamlit as st
from agent import HistoryAgent
import os
from dotenv import load_dotenv

load_dotenv()

# Инициализация сессии
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = HistoryAgent(base_url=os.getenv("OPENAI_API_BASE"))

st.title("Альтернативная История России")

# Боковая панель с выбором чата
with st.sidebar:
    st.header("Чаты")
    if st.button("Новый чат"):
        st.session_state.messages = []
    
    # Здесь можно добавить список сохраненных чатов
    st.markdown("---")
    st.markdown("### Сохраненные чаты")
    # TODO: Добавить функционал сохранения и загрузки чатов

# Основной чат
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("Источники"):
                for source in message["sources"]:
                    st.markdown(f"**Вопрос:** {source['question']}")
                    st.markdown(f"**Результат:** {source['result']}")
                    st.markdown("---")

# Поле ввода
if prompt := st.chat_input("Задайте вопрос об альтернативной истории"):
    # Добавляем сообщение пользователя
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Получаем ответ от агента
    with st.chat_message("assistant"):
        with st.spinner("Анализирую исторические данные..."):
            response = st.session_state.agent.process_query(prompt)
            
            # Отображаем ответ
            st.markdown(response["answer"])
            
            # Отображаем источники
            with st.expander("Источники и анализ"):
                st.markdown("### Вспомогательные вопросы:")
                for question in response["subquestions"]:
                    st.markdown(f"- {question}")
                
                st.markdown("### Найденная информация:")
                for source in response["sources"]:
                    st.markdown(f"**Вопрос:** {source['question']}")
                    st.markdown(f"**Результат:** {source['result']}")
                    st.markdown("---")
    
    # Сохраняем ответ в истории
    st.session_state.messages.append({
        "role": "assistant",
        "content": response["answer"],
        "sources": response["sources"]
    }) 