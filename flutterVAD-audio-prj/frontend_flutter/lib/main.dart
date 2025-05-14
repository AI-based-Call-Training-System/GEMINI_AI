import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:permission_handler/permission_handler.dart';

final recorder = FlutterSoundRecorder();
final ws = WebSocketChannel.connect(Uri.parse("ws://YOUR_SERVER_IP:8000/ws/audio")); // ⚠️ IP 바꿔줘

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Permission.microphone.request();
  await recorder.openRecorder();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: RecorderScreen(),
    );
  }
}

class RecorderScreen extends StatefulWidget {
  @override
  State<RecorderScreen> createState() => _RecorderScreenState();
}

class _RecorderScreenState extends State<RecorderScreen> {
  bool isRecording = false;

  void startStream() async {
    await recorder.startRecorder(
      codec: Codec.pcm16, // raw PCM
      sampleRate: 16000,
      numChannels: 1,
      bitRate: 16000,
      toStream: (buffer) {
        if (buffer != null) {
          ws.sink.add(buffer);
        }
      },
    );
  }

  void stopStream() async {
    await recorder.stopRecorder();
  }

  void listenResponse() {
    ws.stream.listen((event) {
      print('🎧 서버 응답: $event');
      // 응답이 mp3 URL이면 AudioPlayer로 재생도 가능!
    });
  }

  @override
  void initState() {
    super.initState();
    listenResponse();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('🎤 Gemini 음성 대화')),
      body: Center(
        child: ElevatedButton(
          onPressed: () {
            setState(() => isRecording = !isRecording);
            isRecording ? startStream() : stopStream();
          },
          child: Text(isRecording ? "🛑 Stop" : "🎙️ Start"),
        ),
      ),
    );
  }
}
