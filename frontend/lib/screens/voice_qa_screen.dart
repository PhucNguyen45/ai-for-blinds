import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../utils/responsive.dart';
import '../widgets/pulse_circle.dart';
import '../widgets/conversation_bubble.dart';
import '../widgets/glass_bottom_sheet.dart';
import '../widgets/neon_button.dart';
import '../widgets/waveform_bar.dart';

/// Neon Pulse voice Q&A screen with conversation UI.
///
/// Uses [PulseCircle] for visual voice state, [ConversationList] for
/// chat-bubble Q&A display, and [GlassBottomSheetContainer] anchored
/// at the bottom with action buttons.
class VoiceQAScreen extends StatefulWidget {
  const VoiceQAScreen({super.key});

  @override
  State<VoiceQAScreen> createState() => _VoiceQAScreenState();
}

class _VoiceQAScreenState extends State<VoiceQAScreen> {
  final _apiService = ApiService();
  bool _isRecording = false;
  bool _isProcessing = false;
  String? _question;
  String? _answer;
  String? _source;

  // ─── Recording / Q&A logic ───────────────────────────────

  Future<void> _startRecording() async {
    final audio = context.read<AudioService>();
    final hasPermission = await audio.requestMicPermission();
    if (!hasPermission) {
      _showSnackBar('Cần quyền micro để ghi âm.');
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
      try {
        // Step 1: STT — transcribe audio to text via backend
        final audioFile = File(path);
        final sttResult = await _apiService.sttAudio(audioFile);

        if (!mounted) return;

        if (sttResult == null || sttResult.trim().isEmpty) {
          setState(() => _isProcessing = false);
          audio.stop();
          audio.speak('Không nhận dạng được giọng nói, vui lòng thử lại.');
          return;
        }

        final questionText = sttResult.trim();

        // Step 2: RAG — query knowledge base with transcribed text
        final ragResult = await _apiService.ragQuery(question: questionText);

        if (!mounted) return;

        if (ragResult != null) {
          final answerText = ragResult['answer'] as String? ?? '';
          final sourceMap = ragResult['source'] as Map<String, dynamic>?;

          String? sourceText;
          if (sourceMap != null) {
            final parts = <String>[];
            final subject = sourceMap['subject'] as String?;
            final grade = sourceMap['grade'];
            final chapter = sourceMap['chapter'] as String?;
            final page = sourceMap['page_number'];

            if (subject != null && grade != null) {
              parts.add('SGK $subject $grade');
            } else if (subject != null) {
              parts.add('SGK $subject');
            }
            if (chapter != null) parts.add(chapter);
            if (page != null) parts.add('trang $page');
            if (parts.isNotEmpty) sourceText = parts.join(', ');
          }

          setState(() {
            _question = questionText;
            _answer = answerText;
            _source = sourceText;
            _isProcessing = false;
          });

          HapticFeedback.heavyImpact();
          audio.stop();
          if (sourceText != null) {
            audio.speak('$answerText. Nguồn: $sourceText');
          } else {
            audio.speak(answerText);
          }
        } else {
          setState(() => _isProcessing = false);
          audio.stop();
          audio.speak(
            'Không tìm thấy câu trả lời trong sách giáo khoa, vui lòng thử lại.',
          );
        }
      } catch (e) {
        debugPrint('Voice QA error: $e');
        if (!mounted) return;
        setState(() => _isProcessing = false);
        audio.stop();
        audio.speak(
          'Có lỗi xảy ra khi xử lý câu hỏi, vui lòng thử lại.',
        );
      }
    } else {
      if (mounted) {
        setState(() => _isProcessing = false);
        audio.stop();
        audio.speak('Có lỗi khi ghi âm. Xin thử lại.');
      }
    }
  }

  void _speakResult() {
    if (_answer == null) return;
    final audio = context.read<AudioService>();
    audio.stop();
    if (_source != null) {
      audio.speak('$_answer. Nguồn: $_source');
    } else {
      audio.speak(_answer!);
    }
  }

  void _resetAndPrompt() {
    setState(() {
      _question = null;
      _answer = null;
      _source = null;
    });
    final audio = context.read<AudioService>();
    audio.stop();
    audio.speak('Hãy nhấn giữ nút để đặt câu hỏi mới.');
  }

  void _showSnackBar(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), duration: const Duration(seconds: 2)),
    );
  }

  // ─── Build ────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF0A0E1A),
      child: SafeArea(
        child: Column(
          children: [
            // ── Top bar ──────────────────────────────────────
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () {
                      context.read<AudioService>().stop();
                      Navigator.pop(context);
                    },
                    child: const Icon(
                      Icons.arrow_back_rounded,
                      size: 32,
                      color: Color(0xFFFFFFFF),
                    ),
                  ),
                  const Spacer(),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        'Hỏi đáp kiến thức',
                        style: TextStyle(
                          fontSize: Responsive.textScale(context, 24, min: 18, max: 28),
                          fontWeight: FontWeight.bold,
                          color: Color(0xFFFFFFFF),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Hỏi bài bằng giọng nói',
                        style: TextStyle(
                          fontSize: Responsive.textScale(context, 14, min: 12, max: 18),
                          color: Color(0xFF8892B0),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // ── Body area (state-dependent) ─────────────────
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    // Q&A result (conversation view)
    if (_question != null && _answer != null) {
      return _buildConversationView();
    }

    // Processing state
    if (_isProcessing) {
      return _buildProcessingView();
    }

    // Recording state
    if (_isRecording) {
      return _buildRecordingView();
    }

    // Empty / idle state
    return _buildEmptyState();
  }

  Widget _buildEmptyState() {
    return Column(
      children: [
        PulseCircle(
          state: PulseState.idle,
          size: Responsive.safeButtonSize(context, 180, min: 120, max: 200),
          onTap: _startRecording,
          showLabel: false,
        ),
        const SizedBox(height: 24),
        Text(
          'Nhấn giữ để hỏi',
          style: TextStyle(
            fontSize: Responsive.textScale(context, 22, min: 16, max: 26),
            fontWeight: FontWeight.bold,
            color: Color(0xFF8892B0),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Nhấn giữ nút để ghi âm câu hỏi',
          style: TextStyle(
            fontSize: Responsive.textScale(context, 16, min: 13, max: 20),
            color: Color(0xFF4A5580),
          ),
        ),
        const Spacer(flex: 1),
      ],
    );
  }

  Widget _buildRecordingView() {
    return Column(
      children: [
        PulseCircle(
          state: PulseState.listening,
          size: 180,
          onTap: _stopRecordingAndAsk,
          showLabel: false,
        ),
        const SizedBox(height: 24),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16),
          child: WaveformBar(
            state: WaveformState.active,
            height: 40,
          ),
        ),
        const Spacer(flex: 1),
      ],
    );
  }

  Widget _buildProcessingView() {
    return Column(
      children: [
        PulseCircle(
          state: PulseState.processing,
          size: 120,
          showLabel: false,
        ),
        const SizedBox(height: 24),
        const WaveformBar(
          state: WaveformState.processing,
          height: 40,
        ),
        const SizedBox(height: 16),
        Text(
          'Đang tra cứu kiến thức...',
          style: TextStyle(
            fontSize: Responsive.textScale(context, 20, min: 15, max: 24),
            color: Color(0xFFFFB300),
          ),
        ),
        const Spacer(flex: 1),
      ],
    );
  }

  Widget _buildConversationView() {
    return Column(
      children: [
        Expanded(
          child: ConversationList(
            messages: [
              ConversationMessage(
                content: _question!,
                isUser: true,
                timestamp: 'Vừa xong',
              ),
              ConversationMessage(
                content: _answer!,
                isUser: false,
                source: _source,
                timestamp: 'Vừa xong',
              ),
            ],
          ),
        ),
        SizedBox(
          height: 100,
          child: GlassBottomSheetContainer(
            showDragHandle: false,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                NeonIconButton(
                  icon: Icons.volume_up_rounded,
                  label: 'Nghe lại',
                  color: const Color(0xFF00F0FF),
                  onTap: _speakResult,
                ),
                NeonIconButton(
                  icon: Icons.mic_rounded,
                  label: 'Hỏi khác',
                  color: const Color(0xFF39FF14),
                  onTap: _resetAndPrompt,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
