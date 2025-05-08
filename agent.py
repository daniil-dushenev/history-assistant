from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv
import time
import asyncio
from serpapi import GoogleSearch
import json
import requests
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import streamlit as st

load_dotenv()

class HistoryAgent:
    def __init__(self, base_url: str):
        self.llm = ChatOpenAI(
            base_url=base_url,
            model="gpt-4o",
            temperature=0.7
        )
        
        # Инструменты для агента
        self.tools = [
            Tool(
                name="search",
                func=self.google_search,
                description="Поиск информации в интернете"
            ),
            Tool(
                name="create_plot",
                func=self.create_plot,
                description="Создание произвольных графиков с помощью matplotlib. Принимает Python-код для создания графика."
            )
        ]
        
        # Промпт для агента
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Ты - эксперт по истории России, который анализирует альтернативные сценарии развития исторических событий.
            Твоя задача - давать обоснованные ответы на основе реальных исторических фактов и научных исследований.
            Если запрос касается сценария, который не обсуждался в научной литературе, честно признай это.
            Всегда указывай источники информации и обосновывай свои выводы.
            
            Если в запросе упоминается визуализация, график или диаграмма:
            1. Сначала напиши текстовый ответ
            2. Затем ОБЯЗАТЕЛЬНО создай график с помощью инструмента create_plot
            3. Для создания графика используй следующий формат:
               create_plot(
               import matplotlib.pyplot as plt
               import numpy as np
               # Твой код для создания графика
               )
            4. НЕ включай код или данные графика в текстовый ответ
            5. НЕ используй тройные кавычки в коде"""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Создание агента
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    def google_search(self, query: str) -> str:
        """Выполняет поиск через Google Search API"""
        try:
            url = "https://google.serper.dev/search"
            
            payload = json.dumps({
                "q": query,
                "gl": "ru",
                "hl": "ru",
                "num": 5  # Количество результатов
            })
            
            headers = {
                'X-API-KEY': os.getenv("SERPAPI_API_KEY"),
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload)
            results = response.json()
            
            if "error" in results:
                return f"Ошибка поиска: {results['error']}"
            
            # Форматируем результаты
            formatted_results = []
            if "organic" in results:
                for result in results["organic"]:
                    formatted_results.append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", "")
                    })
            
            return json.dumps(formatted_results, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"Ошибка при выполнении поиска: {str(e)}"

    def generate_subquestions(self, query: str) -> List[str]:
        """Генерация вспомогательных вопросов для исследования"""
        prompt = f"""На основе основного вопроса: "{query}"
        Сгенерируй список из 2-3 вспомогательных вопросов, которые помогут найти информацию для ответа.
        Вопросы должны быть конкретными и направленными на поиск исторических фактов."""
        
        response = self.llm.invoke(prompt)
        return [q.strip() for q in response.content.split('\n') if q.strip()]

    def create_plot(self, plot_code: str) -> str:
        """Создает график на основе предоставленного Python-кода"""
        try:
            print("Debug: Полученный код для графика:", plot_code)
            
            # Очищаем код от plt.show() и лишнего текста
            plot_code = plot_code.split('plt.show()')[0].strip()
            if 'График' in plot_code:
                plot_code = plot_code.split('График')[0].strip()
            
            print("Debug: График очищен")
            
            # Создаем новый график
            plt.figure(figsize=(10, 6))
            print("Debug: Создан новый график")
            
            # Безопасное выполнение кода
            safe_globals = {
                'plt': plt,
                'np': np,
                'json': json,
                'io': io,
                'base64': base64,
                'st': st  # Добавляем st в глобальные переменные
            }
            print("Debug: Создан словарь для безопасного выполнения кода")
            
            # Выполняем код для создания графика
            exec(plot_code, safe_globals)
            print("Debug: Выполнен код для создания графика")
            
            # Сохраняем график в байтовый поток
            img = io.BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight', dpi=300)
            img.seek(0)
            print("Debug: График сохранен в байтовый поток")
            
            # Отображаем график в Streamlit
            st.image(img)
            print("Debug: График отображен в Streamlit")
            
            # Очищаем текущий график
            plt.close()
            print("Debug: График очищен")
            
            # Возвращаем только код, а не сам график
            return plot_code
            
        except Exception as e:
            print(f"Debug: Ошибка при создании графика: {str(e)}")
            return f"Ошибка при создании графика: {str(e)}"

    def process_query(self, query: str) -> Dict:
        """Обработка пользовательского запроса"""
        # Генерация вспомогательных вопросов
        subquestions = self.generate_subquestions(query)
        
        # Поиск информации по каждому вопросу
        search_results = []
        for question in subquestions:
            result = self.google_search(question)
            search_results.append({
                "question": question,
                "result": result
            })
            time.sleep(2)  # Небольшая задержка между запросами
        
        # Формирование финального ответа
        final_prompt = f"""На основе следующей информации ответь на вопрос: "{query}"

        Найденная информация:
        {search_results}

        Сформулируй ответ, который:
        1. Будет основан только на реальных исторических фактов
        2. Включит ссылки на источники
        3. Будет содержать обоснованные рассуждения
        4. Если информации недостаточно, честно признай это
        
        Если в запросе упоминается визуализация, график или диаграмма:
        1. Сначала напиши текстовый ответ
        2. Затем ОБЯЗАТЕЛЬНО создай график с помощью инструмента create_plot
        3. Для создания графика используй следующий формат:
           create_plot(
           import matplotlib.pyplot as plt
           import numpy as np
           # Твой код для создания графика
           )
        4. НЕ включай код или данные графика в текстовый ответ
        5. НЕ используй тройные кавычки в коде"""
        
        response = self.agent_executor.invoke({
            "input": final_prompt
        })
        
        # Извлекаем код графика из ответа, если он есть
        plot_code = None
        answer_text = response["output"]
        
        # Ищем последний вызов create_plot в scratchpad
        if "agent_scratchpad" in response:
            scratchpad = response["agent_scratchpad"]
            print("Debug: Scratchpad содержимое:", scratchpad)
            
            if isinstance(scratchpad, str):
                # Ищем последний вызов create_plot
                if "create_plot" in scratchpad:
                    print("Debug: Найден вызов create_plot")
                    # Извлекаем код между скобками
                    parts = scratchpad.split("create_plot")
                    if len(parts) > 1:
                        last_part = parts[-1]
                        print("Debug: Последняя часть после create_plot:", last_part)
                        
                        # Ищем код между скобками
                        if '(' in last_part and ')' in last_part:
                            start = last_part.find('(') + 1
                            end = last_part.rfind(')')
                            if start < end:
                                plot_code = last_part[start:end].strip()
                                # Удаляем все после следующего вызова инструмента
                                if "Tool:" in plot_code:
                                    plot_code = plot_code.split("Tool:")[0].strip()
                                print("Debug: Найден код между скобками:", plot_code)
        
        print("Debug: Итоговый код графика:", plot_code)
        
        return {
            "answer": answer_text.strip(),
            "sources": search_results,
            "subquestions": subquestions,
            "plot_code": plot_code
        } 