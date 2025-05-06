import os
import json
import random
import re
import tempfile
import shutil
import asyncio
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydub import AudioSegment
from openai import OpenAI
from google.cloud import texttospeech
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _sync_generate_text_from_vocab(df, client, model, system_prompt, user_template, max_tokens):
    words = df['words'].dropna().astype(str).tolist()
    vocab = ", ".join(words)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system", "content": system_prompt},
            {"role":"user",   "content": user_template.format(vocab=vocab)},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
        top_p=1.0,
    )
    return resp.choices[0].message.content

async def generate_text_from_vocab(df, client, model="gpt-4o",
                                   system_prompt="You are a helpful assistant.",
                                   user_template="Create an interesting text using these words and idioms: {vocab}.",
                                   max_tokens=1024):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _sync_generate_text_from_vocab,
        df, client, model, system_prompt, user_template, max_tokens
    )

# --- Асинхронные обёртки для LLM ---
# async def generate_text_from_vocab(
#     df: pd.DataFrame,
#     client: OpenAI,
#     model: str = "gpt-4o",
#     system_prompt: str = "You are a helpful assistant.",
#     user_template: str = (
#         "Create an interesting text using these words and idioms: {vocab}. "
#         "In your response there must be only generated text with no hellos, good-byes or any other comments."
#     ),
#     max_tokens: int = 1024,
# ) -> str:
#     words = df['words'].dropna().astype(str).tolist()
#     vocab = ", ".join(words)
#     messages = [
#         {"role": "system", "content": system_prompt},
#         {"role": "user",   "content": user_template.format(vocab=vocab)},
#     ]
#     resp = await client.chat.completions.acreate(
#         model=model,
#         messages=messages,
#         max_tokens=max_tokens,
#         temperature=0.7,
#         top_p=1.0,
#     )
#     return resp.choices[0].message.content

def _sync_generate_interview_qa(text, client, model, system_prompt, max_tokens):
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user",  "content":(
                "Here is the text for interview creation:\n\n"
                f"{text}\n\n"
                "Please create 5-7 interesting questions for a podcast based on the text, "
                "and write the expert answers.\n"
                "Format:\nQ: <question>\nA: <answer>\n"
            )},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
        top_p=1.0,
    )
    return resp.choices[0].message.content

async def generate_interview_qa(text, client, model="gpt-4o",
                                system_prompt="You are a journalist and an expert in creating interviews.",
                                max_tokens=2048):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _sync_generate_interview_qa,
        text, client, model, system_prompt, max_tokens
    )

# async def generate_interview_qa(
#     text: str,
#     client: OpenAI,
#     model: str = "gpt-4o",
#     system_prompt: str = "You are a journalist and an expert in creating interviews.",
#     max_tokens: int = 2048,
# ) -> str:
#     messages = [
#         {"role": "system", "content": system_prompt},
#         {
#             "role": "user",
#             "content": (
#                 "Here is the text for interview creation:\n\n"
#                 f"{text}\n\n"
#                 "Please create 5-7 interesting questions for a podcast based on the text, "
#                 "and write the expert answers.\n"
#                 "Format:\nQ: <question>\nA: <answer>\n"
#             )
#         }
#     ]
#     resp = await client.chat.completions.acreate(
#         model=model,
#         messages=messages,
#         max_tokens=max_tokens,
#         temperature=0.7,
#         top_p=1.0,
#     )
#     return resp.choices[0].message.content

def _sync_humanize_dialogue(qa_text, client, model, system_prompt):
    user_prompt = (
        "Here is the original Q&A:\n\n"
        f"{qa_text}\n\n"
        "Rewrite this as a live conversation between Interviewer and Guest. "
        "Return strictly a JSON array of objects with fields:\n"
        "  - speaker: \"Interviewer\" or \"Guest\"\n"
        "  - text: the utterance\n"
        "Do not add any extra text—only the JSON array."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system", "content":system_prompt},
            {"role":"user",   "content":user_prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
        top_p=1.0,
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```+json\s*|\s*```+$", "", raw, flags=re.IGNORECASE).strip()
    start = raw.find('['); end = raw.rfind(']')
    if start<0 or end<0:
        raise ValueError(f"Can't find JSON in:\n{raw}")
    return json.loads(raw[start:end+1])

async def humanize_dialogue(qa_text, client, model="gpt-4o",
                            system_prompt: str = (
        "You are a scriptwriter and dialogue editor. "
        "Transform the Q&A into a lively, natural-sounding interview with "
        "pauses, interruptions, interjections, clarifications, and genuine reactions."
    )):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _sync_humanize_dialogue,
        qa_text, client, model, system_prompt
    )

# async def humanize_dialogue(
#     qa_text: str,
#     client: OpenAI,
#     model: str = "gpt-4o",
#     system_prompt: str = (
#         "You are a scriptwriter and dialogue editor. "
#         "Transform the Q&A into a lively, natural-sounding interview with "
#         "pauses, interruptions, interjections, clarifications, and genuine reactions."
#     ),
# ) -> list[dict]:
#     user_prompt = (
#         "Here is the original Q&A:\n\n"
#         f"{qa_text}\n\n"
#         "Rewrite this as a live conversation between Interviewer and Guest. "
#         "Return strictly a JSON array of objects with fields:\n"
#         "  - speaker: \"Interviewer\" or \"Guest\"\n"
#         "  - text: the utterance\n"
#         "Do not add any extra text—only the JSON array."
#     )
#     resp = await client.chat.completions.acreate(
#         model=model,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user",   "content": user_prompt},
#         ],
#         temperature=0.7,
#         max_tokens=4096,
#         top_p=1.0,
#     )
#     raw = resp.choices[0].message.content.strip()

#     # Strip markdown fences and extract JSON array
#     raw = re.sub(r"^```+json\s*|\s*```+$", "", raw, flags=re.IGNORECASE).strip()
#     start = raw.find('[')
#     end   = raw.rfind(']')
#     if start == -1 or end == -1:
#         raise ValueError(f"JSON array not found in model output:\n{raw}")
#     json_str = raw[start:end+1]
#     return json.loads(json_str)


# --- Синхронная функция для TTS и склейки ---
def tts_google(
    text: str,
    output_path: str,
    lang_code: str = "en-US",
    voice_name: str = "en-US-Chirp3-HD-Zephyr"
):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_code, name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    resp = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    with open(output_path, "wb") as f:
        f.write(resp.audio_content)


def generate_podcast_from_dialog(
    dialog: list[dict],
    interviewer_voice: str,
    guest_voice: str,
    lang_code: str = "en-US",
    max_pause_ms: int = 200,
    temp_dir: str = None,
    final_output_path: str = "podcast_full.mp3"
) -> str:
    # Prepare temp directory
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    Path(temp_dir).mkdir(parents=True, exist_ok=True)

    audio_files = []
    for idx, turn in enumerate(dialog):
        speaker = turn["speaker"]
        text    = turn["text"]
        voice   = interviewer_voice if speaker.lower().startswith("interviewer") else guest_voice
        out_fp  = Path(temp_dir) / f"turn_{idx:02d}_{speaker}.mp3"
        tts_google(text, str(out_fp), lang_code=lang_code, voice_name=voice)
        audio_files.append(str(out_fp))

    # Concatenate with random pauses
    combined = AudioSegment.empty()
    for fp in audio_files:
        seg = AudioSegment.from_file(fp, format="mp3")
        combined += seg
        pause_ms = random.randint(0, max_pause_ms)
        combined += AudioSegment.silent(duration=pause_ms)

    combined.export(final_output_path, format="mp3")
    return final_output_path


# --- FastAPI endpoint ---
@app.post("/generate-podcast/", response_class=FileResponse)
async def generate_podcast_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    # Validate CSV
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    # Create a unique temp dir per request
    tmpdir = tempfile.mkdtemp()
    try:
        # 1. CSV → DataFrame
        df = pd.read_csv(file.file)

        # 2. Pipeline: vocab → text → Q&A → dialogue (await)
        text = await generate_text_from_vocab(df, openai_client)
        qa   = await generate_interview_qa(text, openai_client)
        dialog = await humanize_dialogue(qa, openai_client)

        # 3. Voices from env or defaults
        interviewer_voice = os.getenv("INTERVIEWER_VOICE", "en-US-Wavenet-F")
        guest_voice       = os.getenv("GUEST_VOICE",       "en-US-Wavenet-D")

        # 4. Generate podcast audio
        loop = asyncio.get_running_loop()
        final_mp3 = await loop.run_in_executor(
            None,
            generate_podcast_from_dialog,
            dialog, 
            interviewer_voice, 
            guest_voice, 
            "en-US", 
            200, 
            tmpdir, 
            str(Path(tmpdir) / "podcast.mp3")
        )

        # 5. Очистка после ответа
        background_tasks.add_task(shutil.rmtree, tmpdir, True)

        return FileResponse(
            path=final_mp3,
            media_type="audio/mpeg",
            filename="podcast.mp3"
        )

    except Exception as e:
        shutil.rmtree(tmpdir, True)
        raise HTTPException(status_code=500, detail=str(e))