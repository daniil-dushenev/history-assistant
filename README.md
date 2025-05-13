# Альтернативная История России

Примеры работы приложения: 
![telegram-cloud-photo-size-2-5251258678491868239-y](https://github.com/user-attachments/assets/c0c129d2-8c1a-494d-93f7-8a5d8c32fff1)



Веб-приложение для моделирования альтернативных сценариев развития исторических событий России с использованием ИИ.

## Установка



1. Клонируйте репозиторий
```bash
git clone https://github.com/daniil-dushenev/history-assistant
cd history-assistant
```
2. Установите зависимости в виртуальное окружение:
```bash
python -m venv env
source ./env/bin/activate
pip install -r requirements.txt
```
3. Создайте файл `.env` и добавьте в него:

Если у вас возникают проблемы с доступом к ключу, вы [можете найти его на платформе](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key)
Для доступа к апи ключу можете воспользоваться контактам разработчиков, мы предоставим ключ использованный для тестов и разработки
```
OPENAI_API_BASE=your_base_url_here
OPENAI_API_KEY=your_api_key_here
SERPAPI_API_KEY=
```

## Запуск:

```bash
streamlit run app.py
```

## Функциональность:

- Чат-интерфейс для задавания вопросов об альтернативной истории
- Анализ исторических данных с использованием ИИ
- Поиск и обработка информации из достоверных источников
- Отображение источников и обоснований ответов
- Возможность сохранения и загрузки чатов

## Технологии:

- Python
- Streamlit
- LangChain
- OpenAI API

## Контакты разработчиков:

- @daniil_d_d: Душенев Даниил
- @sapf3ar: Кузнецов Данил
