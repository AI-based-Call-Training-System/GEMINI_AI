import sounddevice as sd
import asyncio
import websockets

async def send_audio():
    uri = "ws://localhost:8000/ws/audio"
    async with websockets.connect(uri) as ws:
        def callback(indata, frames, time, status):
            asyncio.create_task(ws.send(indata.tobytes()))

        with sd.InputStream(channels=1, samplerate=16000, dtype='int16', callback=callback):
            await asyncio.Future()  # 계속 유지

asyncio.run(send_audio())
