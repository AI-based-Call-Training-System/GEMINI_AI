from google.cloud import texttospeech
import uuid

import os

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] =os.getenv("STT_API_KEY")

def text_to_speech(text: str, output_dir="output") -> str:
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    filename = f"{output_dir}/tts_{uuid.uuid4().hex}.mp3"
    with open(filename, "wb") as out:
        out.write(response.audio_content)

    return filename  # mp3 파일 경로 반환
