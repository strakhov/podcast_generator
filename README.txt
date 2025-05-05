Для запуска:


0.1) Создай файл .env в корне проекта со следующим содержимым (без кавычек):

OPENAI_API_KEY=sk-...
GOOGLE_CREDENTIALS_FILE=podcast-generator-458516-be67f9964d96.json

# опционально, если хотите задать другие голоса:
# INTERVIEWER_VOICE=en-US-Wavenet-F #если не указать, возьмет значение по умолчанию
# GUEST_VOICE=en-US-Wavenet-D #если не указать, возьмет значение по умолчанию

0.2) рядом с .env файлом положи podcast-generator-458516-be67f9964d96.json

1) положить в папку input csv-файл со столбцом words, в котором перечислены ключевые слова, идиомы, etc

2) docker-compose up -d --build


Либо сборка/запуск через Dockerfile:
2) 
# Сборка образа
docker build -t podcast-service .

3)
# Запуск контейнера
docker run -d \
  --name podcast-service \
  -p 8000:8000 \
  -v /путь/до/google_creds.json:/app/podcast-generator-458516-be67f9964d96.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/podcast-generator-458516-be67f9964d96.json \
  -e OPENAI_API_KEY="sk-ВАШ_КЛЮЧ" \
  podcast-service

4) забрать готовый подкаст в папке output