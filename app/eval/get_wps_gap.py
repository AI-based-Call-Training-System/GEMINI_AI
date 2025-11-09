import soundfile as sf
import librosa
from datetime import datetime
import io
from datetime import datetime
from db.database import fs

def parse_timestamp(ts):
    """dict, str, datetime 모두 안전하게 처리"""
    if isinstance(ts, dict) and "$date" in ts:
        return datetime.fromisoformat(ts["$date"].replace("Z", "+00:00"))
    elif isinstance(ts, str):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    elif isinstance(ts, datetime):
        return ts
    else:
        raise ValueError(f"지원되지 않는 타입: {type(ts)}")

def calculate_response_delay(history):
    """
    history: [{... 'role': 'user', 'timestamp': ...}, ...]
    사용자 발화 전까지 걸린 시간(초) 계산
    """
    delays = []
    for i in range(1, len(history)):
        prev = history[i-1]
        curr = history[i]

        # 사용자 발화가 아닌 경우 skip
        if curr["role"] != "user":
            continue

        ts_prev = parse_timestamp(prev["timestamp"])
        ts_curr = parse_timestamp(curr["timestamp"])

        delta = (ts_curr - ts_prev).total_seconds()
        delays.append(delta)


    if(len(delays)==0):
        avg_delay=0
    else:
        avg_delay = sum(delays) / len(delays)

    
    if avg_delay>=400:
        gap_explain=f"평균 발화 간극 {avg_delay}ms으로 다소 여유를 갖고 대화를 하는 편입니다 ."
    else :
        gap_explain=f"평균 발화 간극 {avg_delay}ms으로 대화간의 다소 빠르게 대답합니다."

    return {
        "avg_delay":avg_delay,
        "gap_explain": gap_explain  
        }

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


        # return {
        #     "active_speech_sec": active_duration,
        #     "word_count": word_count,
        #     "words_per_sec": words_per_sec,
        #     "words_per_min": words_per_min
        # }

        return {
            "words_per_min": words_per_min,
            
        }

    except Exception as e:
        log(f"⚠️ 오류 발생: {e}")
        return None


def calculate_whole_speech_rate(history):
    rates=[]
    for message in history:
        message_id = message.get("messageId")
        content = message.get("content")
        if not content or not message_id:
            continue

        # 2. GridFS에서 해당 메시지 파일 찾기
        # 파일 이름에 sessionId가 포함되어 있다고 가정
        file_doc = fs.find_one({"filename": {"$regex": f"tester1"}})
        if not file_doc:
            print(f"⚠️ Audio file for {message_id} not found")
            continue

        # 3. 파일을 메모리로 읽기
        audio_bytes = file_doc.read()  # bytes

        # 4. calculate_speech_rate_active 함수 적용
        try:
            result = calculate_speech_rate(audio_bytes, content)
            if result:
                rates.append(result["words_per_min"])
        except Exception as e:
            print(f"⚠️ Error processing {message_id}: {e}")

    # 모델 돌려서 점수 반환 

    avg_rate = int(sum(rates) / len(rates))
    

    if avg_rate>130:
        wpm_explain="보다 빠릅"
    elif avg_rate==130:
        wpm_explain="과 같습"
    else: 
        wpm_explain="보다 느립"
    
    return {
        "avg_rate":avg_rate,
        "rate_explain":wpm_explain
    }

# # 예시 실행
# if __name__ == "__main__":
#     audio_path = "output/chunk/tts_chunk_01.wav"
#     stt_text = "안녕하세요 주문하시겠어요?"
#     result = calculate_speech_rate(audio_path, stt_text)
#     print("\n최종 결과:", result)
