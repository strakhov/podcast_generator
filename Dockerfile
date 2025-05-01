# Используем официальный образ Python
FROM python:3.9.21-slim

# Рабочая директория
WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники
COPY . ./

# Создаём папки input/output, если их нет
RUN mkdir -p input output

# По умолчанию запускаем скрипт генерации подкастов
CMD ["python", "generate_podcast.py"]