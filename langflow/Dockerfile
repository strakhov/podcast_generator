FROM langflowai/langflow:latest

USER root

# Системные зависимости
RUN apt-get update \
 && apt-get install -y ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

# Устанавливаем pip и зависимости в виртуалку
RUN /app/.venv/bin/python -m ensurepip \
 && /app/.venv/bin/python -m pip install --upgrade pip \
 && /app/.venv/bin/python -m pip install --no-cache-dir -r /app/requirements.txt

# Создаём папки под выход и temp
RUN mkdir -p /app/outputs /app/temp

USER root

CMD ["python", "-m", "langflow", "run", "--host", "0.0.0.0", "--port", "7860"]