import os
import shutil
import tempfile
import json
import pandas as pd
import streamlit as st
from pathlib import Path
from openai import OpenAI
from pydub import AudioSegment
from google.cloud import texttospeech
from dotenv import load_dotenv

load_dotenv()

# Задаём путь к JSON‑ключу Google
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS", "podcast-generator-458516-be67f9964d96.json"
)

# Инициализируем OpenAI‑клиент
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Импортируем функции из вашего модуля (предположим, он называется generate_podcast.py)
from generate_podcast import (
    generate_text_from_vocab,
    generate_interview_qa,
    humanize_dialogue,
    generate_podcast_from_dialog,
)

st.set_page_config(page_title="🎙️ Podcast Generator", layout="wide")

st.title("🎙️ Podcast Generator")

# --- Источник входных данных ---
uploaded_file = st.file_uploader(
    "1) Загрузите CSV с наборами слов (столбец 'words')", type="csv"
)
input_text = st.text_area(
    "или вставьте опорный текст для интервью", height=200
)

st.markdown("---")

# --- Настройки генерации ---
system_prompt = st.text_input(
    "Системный prompt для LLM",
    value="You are a helpful assistant that creates interview Q&A"
)

model = "gpt-4o"
st.markdown(f"**Используемая модель LLM:** `{model}`")

available_voices = ["en-US-Wavenet-A", 
                    "en-US-Wavenet-B", 
                    "en-GB-Wavenet-C", 
                    'en-US-Wavenet-D', 
                    'en-US-Wavenet-E', 
                    'en-US-Wavenet-F', 
                    'en-US-Wavenet-G', 
                    'en-US-Wavenet-H', 
                    'en-US-Wavenet-I', 
                    'en-US-Wavenet-J',
                    'en-US-Chirp3-HD-Achernar',
                    'en-US-Chirp3-HD-Achird']

interviewer_voice = st.selectbox("INTERVIEWER_VOICE", available_voices, index=0)
guest_voice = st.selectbox("GUEST_VOICE", available_voices, index=1)

if st.button("🚀 Generate Podcast"):
    # 1) Получаем исходный текст
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Не удалось прочитать CSV: {e}")
            st.stop()
        source_text = generate_text_from_vocab(
            df, openai_client, model, system_prompt, max_tokens=1024
        )
    elif input_text.strip():
        source_text = input_text
    else:
        st.error("Нужно либо загрузить CSV, либо вставить текст")
        st.stop()

    st.markdown("**🔍 Исходный текст для интервью:**")
    st.write(source_text)

    # 2) Генерируем Q&A
    qa = generate_interview_qa(
        source_text, openai_client, model, system_prompt="You are a journalist and an expert in creating interviews."
    )
    st.markdown("**❓ Сгенерированные вопросы и ответы:**")
    st.text(qa)

    # 3) Очеловечиваем диалог
    try:
        dialog = humanize_dialogue(qa, openai_client, model)
    except Exception as e:
        st.error(f"Ошибка при очеловечивании диалога: {e}")
        st.stop()

    st.markdown("**🗨️ Транскрипция диалога:**")
    for turn in dialog:
        speaker = turn["speaker"]
        text    = turn["text"]
        if speaker.lower() == "interviewer":
            st.markdown(f"**Interviewer:** {text}")
        else:
            st.markdown(f"**Guest:** {text}")

    # 4) Генерируем аудио
    tmpdir = tempfile.mkdtemp()
    output_mp3 = Path(tmpdir) / "podcast.mp3"

    try:
        generate_podcast_from_dialog(
            dialog=dialog,
            interviewer_voice=interviewer_voice,
            guest_voice=guest_voice,
            lang_code="en-US",
            max_pause_ms=300,
            temp_dir=tmpdir,
            final_output_path=str(output_mp3),
        )
    except Exception as e:
        st.error(f"Ошибка при синтезе речи: {e}")
        shutil.rmtree(tmpdir, ignore_errors=True)
        st.stop()

    # 5) Встраиваем и даём ссылку на скачивание
    with open(output_mp3, "rb") as f:
        audio_bytes = f.read()

    st.audio(audio_bytes, format="audio/mp3")
    st.download_button(
        "⬇️ Скачать подкаст",
        data=audio_bytes,
        file_name="podcast.mp3",
        mime="audio/mp3"
    )
    # не забываем убрать временные файлы
    shutil.rmtree(tmpdir, ignore_errors=True)