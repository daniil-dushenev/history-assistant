import streamlit as st
from agent import HistoryAgent
import os
from dotenv import load_dotenv
import json
import matplotlib.pyplot as plt
import numpy as np
import io

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

def create_plot_from_code(code: str):
    """Создает график из Python-кода"""
    try:
        st.write("Debug: Начинаю создание графика")
        st.write("Debug: Полученный код:", code)
        print("Debug: Полученный код:", code)
        
        # Очищаем код от plt.show() и лишнего текста
        code = code.split('plt.show()')[0].strip()
        if 'График' in code:
            code = code.split('График')[0].strip()
        
        # Удаляем лишние кавычки в начале и конце
        code = code.strip("'").strip('"').strip()
        
        # Создаем новый график
        plt.figure(figsize=(10, 6))
        
        # Выполняем код
        exec(code)
        
        # Сохраняем график в байтовый поток
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        buf.seek(0)
        print("Debug: График создан, пытаюсь отобразить")
        # Отображаем график
        st.write("Debug: График создан, пытаюсь отобразить")
        st.image(buf)
        
        # Очищаем текущий график
        plt.close()
    except Exception as e:
        st.error(f"Ошибка при создании графика: {str(e)}")
        st.write("Debug: Код, вызвавший ошибку:")
        st.code(code, language='python')

# Основной чат
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Отображаем график, если есть код
        if "plot_code" in message and message["plot_code"]:
            st.markdown("### Визуализация")
            create_plot_from_code(message["plot_code"])
            
            # Отображаем код создания графика
            with st.expander("Код создания графика"):
                st.code(message["plot_code"], language='python')
        
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
            
            # Отображаем график, если есть код
            if response.get("plot_code"):
                st.markdown("### Визуализация")
                create_plot_from_code(response["plot_code"])
                
                # Отображаем код создания графика
                with st.expander("Код создания графика"):
                    st.code(response["plot_code"], language='python')
            
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
        "sources": response["sources"],
        "plot_code": response.get("plot_code")
    }) 