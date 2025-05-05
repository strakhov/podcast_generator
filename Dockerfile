# Используем официальный образ Python
FROM python:3.9-slim

# Системные зависимости для pydub
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

EXPOSE 8000

# Запускаем Uvicorn, указывая файл generate_podcast.py
CMD ["uvicorn", "generate_podcast:app", "--host", "0.0.0.0", "--port", "8000"]