import os
import time
import uuid
import requests
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# URL вашего Langflow-сервиса
BACKEND_URL = st.text_input(
    "Backend URL",
    value=os.getenv("BACKEND_URL", "http://langflow:7860")
)

# Папка, смонтированная как общий volume между контейнерами
OUTPUT_DIR = Path(os.getenv("SHARED_OUTPUT", "./output"))

st.title("🎙️ Podcast Generator")

# --- Источник входных данных ---
uploaded_file = st.file_uploader("1) Загрузите CSV (колонка 'words')", type="csv")
input_text    = st.text_area("2) Или вставьте текст для интервью", height=200)

# --- Параметры генерации ---
length_minutes = st.slider(
    "Желаемая длина подкаста (минуты)",
    min_value=1, max_value=60, value=5
)

st.markdown("---")

# Кнопка старта
if st.button("🚀 Запустить генерацию подкаста"):
    # Валидируем ввод
    if not uploaded_file and not input_text.strip():
        st.error("Нужно либо загрузить CSV, либо вставить текст")
        st.stop()

    # Генерируем уникальный идентификатор задачи
    uid = uuid.uuid4().hex[:8]
    st.write(f"UID задачи: `{uid}`")

    # Подготавливаем payload
    files = None
    data  = {
        "uid": uid,
        "length": length_minutes
    }

    if uploaded_file:
        # CSV с набором слов
        files = {"file": ("words.csv", uploaded_file.getvalue(), "text/csv")}
    else:
        # Текст напрямую
        data["text"] = input_text

    # Отправляем webhook-запрос на запуск конвейера
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/webhook/",
            json=data if files is None else None,
            files=files,
            timeout=10
        )
        resp.raise_for_status()
    except Exception as e:
        st.error(f"Не удалось запустить задачу: {e}")
        st.stop()

    st.success("Задача принята в работу, ожидайте...")

    # Прогресс-бар
    progress = st.progress(0)
    status_text = st.empty()

    target_file = OUTPUT_DIR / f"podcast_{uid}.mp3"
    total_wait = length_minutes * 60  # максимум ждем столько же секунд, сколько длина
    elapsed = 0

    # Опрашиваем файл каждую секунду
    while elapsed < total_wait:
        if target_file.exists():
            progress.progress(100)
            status_text.success("Готово! Ваш подкаст сгенерирован.")
            break

        # Обновляем прогресс как отношение прошедшего времени к max
        pct = int((elapsed / total_wait) * 100)
        progress.progress(pct)
        status_text.info(f"Генерация... ждём файл (elapsed={elapsed}s)")
        time.sleep(1)
        elapsed += 1
    else:
        status_text.error("Превышено время ожидания. Попробуйте ещё раз позже.")
        st.stop()

    # Предлагаем скачать
    with open(target_file, "rb") as f:
        audio_bytes = f.read()

    st.audio(audio_bytes, format="audio/mp3")
    st.download_button(
        "⬇️ Скачать подкаст",
        data=audio_bytes,
        file_name=f"podcast_{uid}.mp3",
        mime="audio/mp3"
    )