import os
from pathlib import Path
import pandas as pd
from gtts import gTTS
from openai import AzureOpenAI
from google.cloud import texttospeech

from keys import LLM_ENDPOINT, LLM_API_KEY, API_VERSION, MODEL_DEPLOYMENT

client = AzureOpenAI(
    api_version=API_VERSION,
    azure_endpoint=LLM_ENDPOINT,
    api_key=LLM_API_KEY,
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_creds.json"

# Функция генерации текста по словарю

def generate_text_from_vocab(
    df: pd.DataFrame,
    client: AzureOpenAI,
    deployment: str,
    system_prompt: str = "You are a helpful assistant.",
    user_template: str = "Create an interesting text using these words and idioms: {vocab}",
    max_tokens: int = 8192,
    temperature: float = 0.7,
    top_p: float = 1.0
) -> str:
    words = df['words'].dropna().astype(str).tolist()
    vocab = ', '.join(words)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_template.format(vocab=vocab)},
    ]

    response = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    )
    return response.choices[0].message.content

# Функция озвучки текста через Google Translate TTS - беспалтно безлимитно
# def tts_gtts(text: str, output_path: Path, lang: str = "en"):
#     tts = gTTS(text=text, lang=lang)
#     tts.save(str(output_path))
#     print(f"Saved podcast: {output_path}")

# Функция озвучки текста через Google Cloud Service
def tts_google(text: str, output_path: str = "output.mp3", lang_code: str = "en-US", voice_name: str = "en-US-Chirp3-HD-Zephyr"):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_code,
        name=voice_name
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    with open(output_path, "wb") as out:
        out.write(response.audio_content)
        # print(f"Сохранено: {output_path}")


def main():
    input_dir = Path('./input')
    output_dir = Path('./output')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ищем все CSV-файлы в папке input
    csv_files = list(input_dir.glob('*.csv'))
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    for csv_file in csv_files:
        print(f"Processing {csv_file.name}...")
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"Failed to read {csv_file.name}: {e}")
            continue

        # Генерируем текст
        try:
            text = generate_text_from_vocab(df, client, MODEL_DEPLOYMENT)
        except Exception as e:
            print(f"Error generating text for {csv_file.name}: {e}")
            continue

        # Формируем имя выходного файла
        output_file = output_dir / f"{csv_file.stem}.mp3"

        # Озвучиваем
        try:
            tts_google(text, output_file, lang_code="en-US")
        except Exception as e:
            print(f"Error generating TTS for {csv_file.name}: {e}")
            continue

    print("All done!")

if __name__ == '__main__':
    main()