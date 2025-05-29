import os
import uuid
from google.cloud import texttospeech
from dotenv import load_dotenv

load_dotenv()

if os.getenv("STT_API_KEY"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("STT_API_KEY")

client = texttospeech.TextToSpeechClient()

DEFAULT_AUDIO_DIR = "output/audio"
CHUNK_AUDIO_DIR = "output/chunk"
os.makedirs(DEFAULT_AUDIO_DIR, exist_ok=True)
os.makedirs(CHUNK_AUDIO_DIR, exist_ok=True)


def text_to_speech(text: str, output_dir: str = DEFAULT_AUDIO_DIR) -> str:
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16  # WAV
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    filename = f"{output_dir}/tts_{uuid.uuid4().hex}.wav"
    with open(filename, "wb") as out:
        out.write(response.audio_content)

    return filename


def get_next_chunk_filename(base_filename="tts_chunk", ext="wav", output_dir=CHUNK_AUDIO_DIR) -> str:
    i = 1
    while True:
        filename = f"{base_filename}_{i:02d}.{ext}"
        filepath = os.path.join(output_dir, filename)
        if not os.path.exists(filepath):
            return filepath
        i += 1


def text_to_speech_chunks(text: str, base_filename="tts_chunk", output_dir=CHUNK_AUDIO_DIR) -> list:
    filepath = get_next_chunk_filename(base_filename, ext="wav", output_dir=output_dir)
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    with open(filepath, "wb") as out:
        out.write(response.audio_content)

    return [filepath]