import soundfile as sf
import librosa
from datetime import datetime
import io

def calculate_speech_rate(audio_bytes: bytes, stt_text: str, top_db: int = 30):
    """BytesIO로 받은 오디오를 분석"""
    def log(step):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {step}")

    try:
        log("0. 오디오 로드 시작")
        audio_io = io.BytesIO(audio_bytes)
        y, sr = sf.read(audio_io, dtype='float32')
        log(f"1. 로드 완료 - 샘플레이트 {sr}, 길이 {len(y)/sr:.2f}s")

        non_silent_intervals = librosa.effects.split(y, top_db=top_db)
        log(f"2. 활성 구간 {len(non_silent_intervals)}개 감지")

        active_duration = sum((end - start) / sr for start, end in non_silent_intervals)
        if active_duration <= 0:
            raise ValueError("활성 구간이 감지되지 않았습니다. top_db 값을 조정하세요.")
        log(f"3. 활성 발화 길이 {active_duration:.2f}s")

        word_count = len(stt_text.strip().split())
        log(f"4. 어절 수 {word_count}개")

        words_per_sec = round(word_count / active_duration, 2)
        words_per_min = round(words_per_sec * 60, 2)
        log(f"5. 발화 속도 계산 완료: {words_per_sec} 어절/초, {words_per_min} 어절/분")

        return {
            "active_speech_sec": round(active_duration, 2),
            "word_count": word_count,
            "words_per_sec": words_per_sec,
            "words_per_min": words_per_min
        }

    except Exception as e:
        log(f"⚠️ 오류 발생: {e}")
        return None

# # 예시 실행
# if __name__ == "__main__":
#     audio_path = "output/chunk/tts_chunk_01.wav"
#     stt_text = "안녕하세요 주문하시겠어요?"
#     result = calculate_speech_rate(audio_path, stt_text)
#     print("\n최종 결과:", result)
