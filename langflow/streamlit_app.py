import os
import time
import uuid
import requests
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# api/v1/webhook/PodcastGenerator
BACKEND_URL = os.getenv("BACKEND_URL", "http://langflow:7860")

# Папка, смонтированная как общий volume между контейнерами
OUTPUT_DIR = Path(os.getenv("SHARED_OUTPUT", "./output"))

st.title("🎙️ Podcast Generator")

# --- Источник входных данных ---
# uploaded_file = st.file_uploader("1) Загрузите CSV (колонка 'words')", type="csv")
input_text    = st.text_area("2) Вставьте текст или набор слов для создания интервью на их основе", height=200)

# --- Выбор голосов для озвучки ---
available_voices = [
    "en-US-Studio-O","en-US-Chirp3-HD-Pulcherrima", "en-US-Wavenet-D", "en-US-Wavenet-C", 
    "en-US-Wavenet-F", "en-US-Wavenet-J", "en-US-Chirp3-HD-Zephyr", "en-US-Standard-B",
    "en-US-Wavenet-E", "en-US-Chirp3-HD-Schedar", "en-US-Chirp3-HD-Gacrux", "en-US-Wavenet-G",
]

# iv = st.selectbox("Interviewer voice", available_voices, index=0)
# gv = st.selectbox("Guest voice",        available_voices, index=1)

# --- Параметры генерации ---
length_minutes = st.slider(
    "Желаемая длина подкаста (минуты)",
    min_value=1, max_value=60, value=5
)

st.markdown("---")

# Кнопка старта
if st.button("🚀 Запустить генерацию подкаста"):
    # Валидируем ввод
    if not input_text.strip():
        st.error("Необходимо вставить текст")
        st.stop()

    # Генерируем уникальный идентификатор задачи
    uid = uuid.uuid4().hex[:8]
    st.write(f"UID задачи: `{uid}`")

    # Подготавливаем payload
    files = None
    data = {
        "uid": uid,
        "length": length_minutes,
        "interviewer_voice": iv,
        "guest_voice": gv
    }

    data["text"] = input_text

    # Отправляем webhook-запрос на запуск конвейера
    
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/webhook/PodcastGenerator",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        resp.raise_for_status()
        execution_id = uid

    except Exception as e:
        st.error(f"Не удалось запустить задачу: {e}")
        st.stop()

    st.success("Задача принята в работу, ожидайте...")

    # Прогресс-бар
    progress = st.progress(0)
    status_text = st.empty()

    target_file = Path("/app/shared/output") / f"podcast_{uid}.mp3"
    total_wait = length_minutes * 60 * 5  # максимум ждем столько же секунд, сколько длина х5
    elapsed = 0

    while elapsed < total_wait:
        if target_file.exists():
            progress.progress(100)
            status_text.success("Готово! Ваш подкаст сгенерирован.")

            dialog_file = Path("/app/shared/output") / f"podcast_dialog_{uid}.txt"
            if dialog_file.exists():
                st.subheader("📝 Транскрипция диалога")
                # читаем весь файл и показываем как preformatted text
                dialog_text = dialog_file.read_text(encoding="utf-8")
                st.text(dialog_text)
            else:
                st.info("Транскрипция пока не готова или файл не найден.")

            # Показываем аудио
            with open(target_file, "rb") as f:
                audio_bytes = f.read()
            
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button(
                "⬇️ Скачать подкаст",
                data=audio_bytes,
                file_name=f"podcast_{uid}.mp3",
                mime="audio/mp3"
            )
            break

        # Обновляем прогресс
        pct = int((elapsed / total_wait) * 100)
        progress.progress(pct)
        status_text.info(f"Генерация... прошло {elapsed} секунд")
        time.sleep(1)
        elapsed += 1
    else:
        status_text.error("Превышено время ожидания. Попробуйте ещё раз позже.")
        st.stop()