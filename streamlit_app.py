import os
import shutil
import tempfile
import requests
import pandas as pd
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = st.text_input(
    "Backend URL", value=os.getenv("BACKEND_URL","http://localhost:8000")
)

st.title("🎙️ Podcast Generator")

# --- Исходные данные ---
uploaded_file = st.file_uploader("Загрузите CSV (колонка 'words')", type="csv")
input_text    = st.text_area("Или вставьте текст для интервью", height=200)

st.markdown("---")
st.markdown("**Используемая модель LLM:** `gpt-4o`")

available_voices = [
    "en-US-Wavenet-A","en-US-Wavenet-B","en-GB-Wavenet-C",
    "en-US-Wavenet-D","en-US-Wavenet-E","en-US-Wavenet-F",
]

iv = st.selectbox("Interviewer voice", available_voices, index=0)
gv = st.selectbox("Guest voice",        available_voices, index=1)

if st.button("🚀 Generate Podcast"):
    # 1) First, get the humanized dialogue JSON
    files = {}
    data  = {}
    if uploaded_file:
        files = {"file": ("words.csv", uploaded_file.getvalue(), "text/csv")}
    elif input_text.strip():
        data = {"text": input_text}
    else:
        st.error("Нужно либо загрузить CSV, либо вставить текст")
        st.stop()

    try:
        r = requests.post(
            f"{BACKEND_URL}/generate-dialogue/",
            files=files or None,
            data = data  or None,
            timeout=120
        )
        r.raise_for_status()
        dialog = r.json()
    except Exception as e:
        st.error(f"Ошибка при получении диалога: {e}")
        st.stop()

    # 2) Показываем транскрипт
    st.markdown("**🗨️ Транскрипция диалога:**")
    for turn in dialog:
        prefix = "**Interviewer:**" if turn["speaker"]=="Interviewer" else "**Guest:**"
        st.markdown(f"{prefix} {turn['text']}")

    # 3) Запрашиваем MP3
    try:
        # повторно шлём либо файл, либо JSON dialogue
        if files:
            # backend сам сгенерит текст→QA→dialogue→аудио
            r2 = requests.post(
                f"{BACKEND_URL}/generate-podcast/",
                files=files,
                timeout=300
            )
        else:
            # отправляем уже готовый диалог JSON
            r2 = requests.post(
                f"{BACKEND_URL}/generate-podcast/",
                json={"dialogue": dialog, "interviewer_voice": iv, "guest_voice": gv},
                timeout=300
            )
        r2.raise_for_status()
        audio_bytes = r2.content
    except Exception as e:
        st.error(f"Ошибка при получении аудио: {e}")
        st.stop()

    # 4) Встраиваем плеер и даём ссылку
    st.audio(audio_bytes, format="audio/mp3")
    st.download_button("⬇️ Скачать подкаст", data=audio_bytes, file_name="podcast.mp3", mime="audio/mp3")