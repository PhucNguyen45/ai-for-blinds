import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import 'dart:io';

import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../theme/app_theme.dart';
import '../widgets/big_button.dart';
import '../widgets/voice_indicator.dart';

/// Screen for voice-based Q&A with RAG knowledge base.
/// Follows the SgBe Vision design spec:
/// - VoiceIndicator (hiệu ứng sóng âm) khi đang nghe
/// - BigButton "NHẤN ĐỂ HỎI" — nhấn giữ để ghi âm, thả để gửi
/// - Vùng hiển thị text câu hỏi và câu trả lời
/// - TTS tự động đọc câu trả lời, kèm trích dẫn nguồn SGK
class VoiceQAScreen extends StatefulWidget {
  const VoiceQAScreen({super.key});

  @override
  State<VoiceQAScreen> createState() => _VoiceQAScreenState();
}

class _VoiceQAScreenState extends State<VoiceQAScreen> {
  final ApiService _apiService = ApiService();
  bool _isRecording = false;
  bool _isProcessing = false;
  String? _question;
  String? _answer;
  String? _source;

  Future<void> _startRecording() async {
    final audio = context.read<AudioService>();
    final hasPermission = await audio.requestMicPermission();
    if (!hasPermission) {
      audio.speak('Ứng dụng cần quyền micro để ghi âm. '
          'Hãy vào phần cài đặt của điện thoại để cấp quyền.');
      return;
    }

    HapticFeedback.heavyImpact();
    audio.stop();
    audio.speak('Đang nghe');

    final path = await audio.startRecording();
    if (path != null) {
      setState(() => _isRecording = true);
    }
  }

  Future<void> _stopRecordingAndAsk() async {
    final audio = context.read<AudioService>();
    final path = await audio.stopRecording();

    setState(() {
      _isRecording = false;
      _isProcessing = true;
    });

    if (path != null) {
      // Bản ghi âm đi qua hai chặng: /stt đổi tiếng nói thành chữ,
      // /rag/query tra sách giáo khoa rồi soạn câu trả lời.
      final question = await _apiService.sttAudio(File(path));

      if (!mounted) return;
      if (question == null || question.trim().isEmpty) {
        setState(() => _isProcessing = false);
        audio.stop();
        audio.speak('Chưa nghe rõ câu hỏi. Hãy nhấn giữ nút và hỏi lại.');
        return;
      }

      setState(() => _question = question);

      final result = await _apiService.ragQuery(question: question);

      if (!mounted) return;
      if (result == null) {
        setState(() => _isProcessing = false);
        audio.stop();
        audio.speak('Không kết nối được máy chủ. Hãy kiểm tra mạng rồi thử lại.');
        return;
      }

      final source = result['source'] is Map
          ? (result['source']['citation'] as String?)
          : null;

      setState(() {
        _answer = result['answer'] as String?;
        _source = source;
        _isProcessing = false;
      });

      HapticFeedback.heavyImpact();
      audio.stop();
      audio.speak(_source == null ? '$_answer' : '$_answer. Nguồn: $_source');
    } else {
      if (mounted) {
        setState(() => _isProcessing = false);
        audio.stop();
        audio.speak('Có lỗi khi ghi âm. Xin thử lại.');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final bgColor = isDark ? AppTheme.pureBlack : AppTheme.pureWhite;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Hỏi đáp kiến thức'),
        backgroundColor: isDark ? AppTheme.pureBlack : AppTheme.primaryBlue,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, size: 32),
          onPressed: () {
            context.read<AudioService>().stop();
            Navigator.pop(context);
          },
        ),
      ),
      body: Container(
        color: bgColor,
        child: Column(
          children: [
            // Voice indicator + record button area
            Container(
              padding: const EdgeInsets.symmetric(vertical: 24),
              color: isDark ? AppTheme.darkCard : Colors.grey.shade50,
              child: Consumer<AudioService>(
                builder: (context, audio, _) {
                  return Column(
                    children: [
                      // Voice indicator (shows when listening/speaking)
                      VoiceIndicator(
                        isSpeaking: audio.isSpeaking,
                        isListening: _isRecording,
                        isPaused: audio.isPaused,
                      ),
                      const SizedBox(height: 20),

                      // Record button — press and hold to ask
                      Semantics(
                        label: 'NHẤN ĐỂ HỎI. Nhấn giữ để ghi âm câu hỏi, thả để gửi.',
                        hint: 'Nhấn giữ để ghi âm',
                        button: true,
                        child: GestureDetector(
                          onLongPressStart: (_) => _startRecording(),
                          onLongPressEnd: (_) => _stopRecordingAndAsk(),
                          child: Container(
                            width: 160,
                            height: 160,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _isRecording
                                  ? AppTheme.accentRed
                                  : AppTheme.accentGreen,
                              border: Border.all(
                                color: Colors.white,
                                width: 4,
                              ),
                            ),
                            child: Icon(
                              _isRecording ? Icons.mic_rounded : Icons.mic_none_rounded,
                              size: 72,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Label
                      Text(
                        _isRecording
                            ? 'Đang nghe...'
                            : (_isProcessing
                                ? 'Đang xử lý...'
                                : 'NHẤN GIỮ ĐỂ HỎI'),
                        style: theme.textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: _isRecording
                              ? AppTheme.accentRed
                              : (_isProcessing
                                  ? AppTheme.accentOrange
                                  : null),
                        ),
                      ),
                      if (!_isRecording && !_isProcessing)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            'Nhấn giữ nút để ghi âm câu hỏi,\nthả nút để gửi và nhận câu trả lời',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey.shade500,
                              height: 1.4,
                            ),
                          ),
                        ),
                    ],
                  );
                },
              ),
            ),

            // Processing indicator
            if (_isProcessing)
              Padding(
                padding: const EdgeInsets.all(24),
                child: Semantics(
                  label: 'Đang xử lý câu hỏi.',
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(
                        width: 28,
                        height: 28,
                        child: CircularProgressIndicator(strokeWidth: 3),
                      ),
                      const SizedBox(width: 16),
                      Text(
                        'Đang tra cứu kiến thức...',
                        style: theme.textTheme.titleMedium,
                      ),
                    ],
                  ),
                ),
              ),

            // Q&A result area
            if (_question != null && _answer != null)
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Question
                      Semantics(
                        label: 'Câu hỏi. $_question',
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryBlue.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: AppTheme.primaryBlue.withValues(alpha: 0.3),
                              width: 2,
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  const Icon(
                                    Icons.volume_up_rounded,
                                    size: 22,
                                    color: AppTheme.primaryBlue,
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Câu hỏi',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                      color: AppTheme.primaryBlue,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _question!,
                                style: theme.textTheme.bodyLarge,
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Answer
                      Semantics(
                        label: 'Câu trả lời. $_answer',
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: isDark ? AppTheme.darkCard : AppTheme.pureWhite,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: isDark ? Colors.grey.shade700 : Colors.grey.shade300,
                              width: 2,
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  const Icon(
                                    Icons.lightbulb_rounded,
                                    size: 22,
                                    color: AppTheme.accentOrange,
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Câu trả lời',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                      color: AppTheme.accentOrange,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _answer!,
                                style: theme.textTheme.bodyLarge?.copyWith(height: 1.6),
                              ),
                              if (_source != null) ...[
                                const SizedBox(height: 12),
                                Row(
                                  children: [
                                    const Icon(
                                      Icons.menu_book_rounded,
                                      size: 18,
                                      color: Colors.grey,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      _source!,
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: Colors.grey.shade500,
                                        fontStyle: FontStyle.italic,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),

                      const SizedBox(height: 16),

                      // Listen again button + new question
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          BigMediaButton(
                            icon: Icons.volume_up_rounded,
                            label: 'Nghe lại',
                            color: AppTheme.accentGreen,
                            onTap: () {
                              context.read<AudioService>().stop();
                              context.read<AudioService>().speak(
                                '$_answer. Nguồn: $_source',
                              );
                            },
                          ),
                          BigMediaButton(
                            icon: Icons.mic_rounded,
                            label: 'Hỏi khác',
                            color: AppTheme.primaryBlue,
                            onTap: () {
                              setState(() {
                                _question = null;
                                _answer = null;
                                _source = null;
                              });
                              final audio = context.read<AudioService>();
                              audio.stop();
                              audio.speak('Hãy nhấn giữ nút để đặt câu hỏi mới.');
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

            // Empty state when no Q&A yet
            if (_question == null && !_isProcessing)
              Expanded(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.mic_rounded,
                          size: 64,
                          color: Colors.grey.shade400,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Chưa có câu hỏi nào.\nNhấn giữ nút để bắt đầu.',
                          textAlign: TextAlign.center,
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: Colors.grey.shade500,
                            height: 1.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
