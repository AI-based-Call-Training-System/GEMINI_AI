import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_sound/flutter_sound.dart';

class AudioStreamService {
  final _channel = WebSocketChannel.connect(
    //애뮬레이터에서 로컬 호스트에 접근하기 위한 특별한 규칙
    //10.0.2.2
    Uri.parse("ws://10.0.2.2:8000/ws/audio"),
  );

  final FlutterSoundRecorder _recorder = FlutterSoundRecorder();

  Future<void> initRecorder() async {
    await _recorder.openRecorder();
    await _recorder.setSubscriptionDuration(const Duration(milliseconds: 30));
  }

  Future<void> startStreaming() async {
    await _recorder.startRecorder(
      codec: Codec.pcm16,
      sampleRate: 16000,
      numChannels: 1,
      bitRate: 16000,
      toStream: (buffer) {
        if (buffer != null) {
          _channel.sink.add(buffer);
        }
      },
    );
  }

  Future<void> stopStreaming() async {
    await _recorder.stopRecorder();
  }

  Stream get responseStream => _channel.stream;

  void dispose() {
    _recorder.closeRecorder();
    _channel.sink.close();
  }
}
