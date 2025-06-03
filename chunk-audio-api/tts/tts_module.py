import os
import uuid
from google.cloud import texttospeech
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()

# STT_API_KEY가 설정되어 있다면 환경 변수로 등록 (Google Cloud 인증용)
if os.getenv("STT_API_KEY"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("STT_API_KEY")

# Google Cloud Text-to-Speech 클라이언트 생성
client = texttospeech.TextToSpeechClient()

# 기본 오디오 출력 디렉토리 설정
DEFAULT_AUDIO_DIR = "output/audio"
CHUNK_AUDIO_DIR = "output/chunk"
os.makedirs(DEFAULT_AUDIO_DIR, exist_ok=True)
os.makedirs(CHUNK_AUDIO_DIR, exist_ok=True)


def text_to_speech(text: str, output_dir: str = DEFAULT_AUDIO_DIR) -> str:
    """
    주어진 텍스트를 TTS로 변환하여 WAV 파일로 저장하고, 해당 파일 경로를 반환함.
    :param text: 변환할 텍스트
    :param output_dir: 저장할 디렉토리
    :return: 저장된 WAV 파일 경로
    """
    os.makedirs(output_dir, exist_ok=True)

    # 텍스트 입력 설정
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # 음성 설정: 한국어, 중립 성별
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # 오디오 출력 설정: LINEAR16(WAV 포맷)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    # TTS 요청 수행
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # 고유한 파일 이름으로 저장
    filename = f"{output_dir}/tts_{uuid.uuid4().hex}.wav"
    with open(filename, "wb") as out:
        out.write(response.audio_content)

    return filename


def get_next_chunk_filename(base_filename="tts_chunk", ext="wav", output_dir=CHUNK_AUDIO_DIR) -> str:
    """
    현재 디렉토리에 존재하지 않는 다음 chunk 파일명을 반환함 (중복 방지).
    :param base_filename: 기본 파일명 접두어
    :param ext: 확장자
    :param output_dir: 저장할 디렉토리
    :return: 생성된 파일 경로 문자열
    """
    i = 1
    while True:
        filename = f"{base_filename}_{i:02d}.{ext}"
        filepath = os.path.join(output_dir, filename)
        if not os.path.exists(filepath):
            return filepath
        i += 1


def text_to_speech_chunks(text: str, base_filename="tts_chunk", output_dir=CHUNK_AUDIO_DIR) -> list:
    """
    주어진 텍스트를 TTS로 변환하여 고유한 chunk 파일로 저장하고, 파일 경로 리스트를 반환함.
    (현재는 한 문장 = 한 chunk 방식)
    :param text: 변환할 텍스트
    :param base_filename: 기본 파일명 접두어
    :param output_dir: 저장 디렉토리
    :return: 저장된 파일 경로 리스트 (현재는 한 개만 반환)
    """
    filepath = get_next_chunk_filename(base_filename, ext="wav", output_dir=output_dir)

    # 텍스트 입력
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # 음성 설정
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # 오디오 출력 설정
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    # TTS 요청 수행
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # chunk 파일로 저장
    with open(filepath, "wb") as out:
        out.write(response.audio_content)

    return [filepath]
