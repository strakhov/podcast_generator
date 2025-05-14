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


4) скачать готовый подкаст



Запуск langflow:

cd langflow/docker_example
docker compose up

Langflow is now accessible at http://localhost:7860/.



Для запуска PodcastGenerator в langflow:

1) внести изменения в Dockerfile и docker-compose.yml - там прописана установка недостающих зависимостей в окружение langflow и др.

2) положить рядом с Dockerfile и docker-compose.yml файлыЖ
 - podcast-generator-458516-be67f9964d96.json с ключами доступа к google.cloud
 - requirements.txt

3) запустить langflow командой
docker compose up

4) вставить OpenAI_API_Key там, где надо

После отработки конвейера mp3-файл с подкастом будет в корневой папке контейнера langflow