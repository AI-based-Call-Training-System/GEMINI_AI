import 'package:flutter/material.dart';
import '../services/audio_stream_service.dart';

class RecorderScreen extends StatefulWidget {
  const RecorderScreen({super.key});

  @override
  State<RecorderScreen> createState() => _RecorderScreenState();
}

class _RecorderScreenState extends State<RecorderScreen> {
  final audioService = AudioStreamService();

  bool isRecording = false;
  String transcript = '';
  String geminiResponse = '';

  @override
  void initState() {
    super.initState();
    audioService.initRecorder();
    audioService.responseStream.listen((msg) {
      final data = msg.toString(); // json 파싱 가능
      print("🔊 서버 응답: $data");

      setState(() {
        transcript = data.contains('transcript') ? data : '';
        geminiResponse = data.contains('response') ? data : '';
      });

      // TODO: mp3 응답이면 자동 재생 처리도 가능
    });
  }

  @override
  void dispose() {
    audioService.dispose();
    super.dispose();
  }

  void toggleRecording() {
    if (isRecording) {
      audioService.stopStreaming();
    } else {
      audioService.startStreaming();
    }

    setState(() {
      isRecording = !isRecording;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🎤 음성 챗봇')),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            Text('📝 인식된 말: $transcript'),
            const SizedBox(height: 10),
            Text('🤖 Gemini 응답: $geminiResponse'),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: toggleRecording,
              icon: Icon(isRecording ? Icons.stop : Icons.mic),
              label: Text(isRecording ? '녹음 중지' : '녹음 시작'),
            )
          ],
        ),
      ),
    );
  }
}
