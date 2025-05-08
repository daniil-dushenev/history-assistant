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
            )
        ]
        
        # Промпт для агента
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Ты - эксперт по истории России, который анализирует альтернативные сценарии развития исторических событий.
            Твоя задача - давать обоснованные ответы на основе реальных исторических фактов и научных исследований.
            Если запрос касается сценария, который не обсуждался в научной литературе, честно признай это.
            Всегда указывай источники информации и обосновывай свои выводы."""),
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
        1. Будет основан только на реальных исторических фактах
        2. Включит ссылки на источники
        3. Будет содержать обоснованные рассуждения
        4. Если информации недостаточно, честно признай это"""
        
        response = self.agent_executor.invoke({
            "input": final_prompt
        })
        
        return {
            "answer": response["output"],
            "sources": search_results,
            "subquestions": subquestions
        } 