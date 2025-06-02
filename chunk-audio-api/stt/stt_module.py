from google.cloud import speech
import os
import wave
import io
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()
# 구글 클라우드 인증키 경로를 환경변수로 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("STT_API_KEY")


def get_sample_rate_from_wav(audio_bytes: bytes) -> int:
    """
    WAV 오디오 바이트에서 샘플링 레이트(샘플링 주파수)를 추출하는 함수
    :param audio_bytes: WAV 파일의 바이너리 데이터
    :return: 샘플링 레이트 (Hz)
    """
    # 메모리 상의 바이트 스트림을 wave 모듈로 열기
    with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
        return wav_file.getframerate()  # 샘플링 주파수 반환


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Google Cloud Speech-to-Text API를 사용해 음성 인식 수행
    :param audio_bytes: WAV 형식의 오디오 바이너리 데이터
    :return: 인식된 텍스트 문자열
    """
    # WAV에서 샘플링 주파수 얻기
    sample_rate = get_sample_rate_from_wav(audio_bytes)
    # Google Speech 클라이언트 생성
    client = speech.SpeechClient()

    # 오디오 데이터를 RecognitionAudio 객체로 생성
    audio = speech.RecognitionAudio(content=audio_bytes)
    # 인식 설정: 인코딩, 샘플레이트, 언어(한국어)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="ko-KR"
    )

    # 동기 음성 인식 요청
    response = client.recognize(config=config, audio=audio)

    result_text = ""
    # 응답에서 각 결과의 최고 대안(가장 높은 확률의 텍스트)을 이어붙임
    for result in response.results:
        result_text += result.alternatives[0].transcript + " "
    # 앞뒤 공백 제거 후 반환
    return result_text.strip()
