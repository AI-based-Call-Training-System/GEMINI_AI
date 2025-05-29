from google.cloud import speech
import os
import wave
import io
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("STT_API_KEY")


def get_sample_rate_from_wav(audio_bytes: bytes) -> int:
    with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
        return wav_file.getframerate()


def transcribe_audio(audio_bytes: bytes) -> str:
    sample_rate = get_sample_rate_from_wav(audio_bytes)
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="ko-KR"
    )

    response = client.recognize(config=config, audio=audio)

    result_text = ""
    for result in response.results:
        result_text += result.alternatives[0].transcript + " "
    return result_text.strip()
