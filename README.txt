Для запуска:


0.1) Создай файл .env в корне проекта со следующим содержимым (без кавычек):

OPENAI_API_KEY=sk-...
GOOGLE_CREDENTIALS_FILE=podcast-generator-458516-be67f9964d96.json

0.2) рядом с .env файлом положи podcast-generator-458516-be67f9964d96.json

1) подготовить csv-файл со столбцом words, в котором перечислены ключевые слова, идиомы, etc. Либо просто набор ключевых слов, тем, опорный текст

2) запуск бэкенд сервиса
docker-compose up -d --build

3) запуск интерфейса
streamlit run streamlit_app.py


4) забрать скачать готовый подкаст