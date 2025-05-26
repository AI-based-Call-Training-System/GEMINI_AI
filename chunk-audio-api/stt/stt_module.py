from google.cloud import speech
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] =os.getenv("STT_API_KEY")

def transcribe_audio(audio_bytes: bytes) -> str:
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ko-KR"
    )

    response = client.recognize(config=config, audio=audio)

    result_text = ""
    for result in response.results:
        result_text += result.alternatives[0].transcript + " "
    return result_text.strip()
