import webrtcvad

vad = webrtcvad.Vad(2)  # 민감도 0~3 (높을수록 민감)

def is_speech_chunk(audio_chunk: bytes, sample_rate=16000, frame_duration=30) -> bool:
    try:
        return vad.is_speech(audio_chunk, sample_rate)
    except:
        return False
