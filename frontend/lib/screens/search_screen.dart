import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../utils/responsive.dart';
import '../widgets/pulse_circle.dart';
import '../widgets/glass_bottom_sheet.dart';
import '../widgets/neon_button.dart';
import '../widgets/waveform_bar.dart';

/// Neon Pulse voice-first search screen.
///
/// Lets the user record a Vietnamese query, transcribes it via the backend
/// STT endpoint, then searches the web + Vietnamese news through the IR
/// backend (`/search`) and reads the top results aloud.
class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _apiService = ApiService();
  bool _isRecording = false;
  bool _isProcessing = false;
  String? _query;
  List<Map<String, dynamic>> _results = const [];

  // ─── Recording / search logic ────────────────────────────

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

  Future<void> _stopRecordingAndSearch() async {
    final audio = context.read<AudioService>();
    final path = await audio.stopRecording();

    setState(() {
      _isRecording = false;
      _isProcessing = true;
    });

    if (path != null) {
      try {
        // Step 1: STT — transcribe the recorded query via backend
        final audioFile = File(path);
        final sttResult = await _apiService.sttAudio(audioFile);

        if (!mounted) return;

        if (sttResult == null || sttResult.trim().isEmpty) {
          setState(() => _isProcessing = false);
          audio.stop();
          audio.speak('Không nhận dạng được giọng nói, vui lòng thử lại.');
          return;
        }

        final queryText = sttResult.trim();

        // Step 2: IR — search the web + Vietnamese news
        final results = await _apiService.searchWeb(queryText, nResults: 5);

        if (!mounted) return;

        if (results.isNotEmpty) {
          setState(() {
            _query = queryText;
            _results = results;
            _isProcessing = false;
          });

          HapticFeedback.heavyImpact();
          audio.stop();
          audio.speak(_buildSpokenResults());
        } else {
          setState(() {
            _query = queryText;
            _results = const [];
            _isProcessing = false;
          });

          audio.stop();
          audio.speak(
            'Không tìm thấy kết quả cho từ khóa $_query. Vui lòng thử lại.',
          );
        }
      } catch (e) {
        debugPrint('Search error: $e');
        if (!mounted) return;
        setState(() => _isProcessing = false);
        audio.stop();
        audio.speak('Có lỗi xảy ra khi tìm kiếm, vui lòng thử lại.');
      }
    } else {
      if (mounted) {
        setState(() => _isProcessing = false);
        audio.stop();
        audio.speak('Có lỗi khi ghi âm. Xin thử lại.');
      }
    }
  }

  /// Build a concise spoken summary of the top results.
  String _buildSpokenResults() {
    if (_results.isEmpty) return 'Không tìm thấy kết quả nào.';

    final spoken = StringBuffer('Tìm thấy ${_results.length} kết quả. ');
    final maxSpeak = _results.length < 3 ? _results.length : 3;
    for (int i = 0; i < maxSpeak; i++) {
      final r = _results[i];
      final title = (r['title'] as String? ?? '').trim();
      final snippet = (r['snippet'] as String? ?? '').trim();
      final source = r['source'] == 'web' ? 'Trang web' : 'Tin tức';
      spoken.write('Kết quả ${i + 1}. $source. ');
      if (title.isNotEmpty) spoken.write('$title. ');
      if (snippet.isNotEmpty) spoken.write('$snippet. ');
    }
    if (_results.length > maxSpeak) {
      spoken.write('Và ${_results.length - maxSpeak} kết quả khác.');
    }
    return spoken.toString();
  }

  void _speakResult() {
    if (_query == null) return;
    final audio = context.read<AudioService>();
    audio.stop();
    audio.speak(_buildSpokenResults());
  }

  void _resetAndPrompt() {
    setState(() {
      _query = null;
      _results = const [];
    });
    final audio = context.read<AudioService>();
    audio.stop();
    audio.speak('Hãy nhấn giữ nút để nói từ khóa cần tìm.');
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
                        'Tìm kiếm thông tin',
                        style: TextStyle(
                          fontSize:
                              Responsive.textScale(context, 24, min: 18, max: 28),
                          fontWeight: FontWeight.bold,
                          color: const Color(0xFFFFFFFF),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Tra cứu Internet bằng giọng nói',
                        style: TextStyle(
                          fontSize:
                              Responsive.textScale(context, 14, min: 12, max: 18),
                          color: const Color(0xFF8892B0),
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
    // Results view
    if (_query != null && _results.isNotEmpty) {
      return _buildResultsView();
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
          'Nhấn giữ để tìm kiếm',
          style: TextStyle(
            fontSize: Responsive.textScale(context, 22, min: 16, max: 26),
            fontWeight: FontWeight.bold,
            color: const Color(0xFF8892B0),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Nhấn giữ nút để nói từ khóa cần tìm',
          style: TextStyle(
            fontSize: Responsive.textScale(context, 16, min: 13, max: 20),
            color: const Color(0xFF4A5580),
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
          onTap: _stopRecordingAndSearch,
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
          'Đang tìm kiếm...',
          style: TextStyle(
            fontSize: Responsive.textScale(context, 20, min: 15, max: 24),
            color: const Color(0xFFFFB300),
          ),
        ),
        const Spacer(flex: 1),
      ],
    );
  }

  Widget _buildResultsView() {
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            itemCount: _results.length + 1,
            itemBuilder: (context, index) {
              if (index == 0) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(
                    'Tìm thấy ${_results.length} kết quả cho "$_query":',
                    style: TextStyle(
                      fontSize: Responsive.textScale(context, 16, min: 13, max: 20),
                      color: const Color(0xFF8892B0),
                    ),
                  ),
                );
              }
              return _SearchResultCard(
                index: index,
                result: _results[index - 1],
              );
            },
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
                  label: 'Tìm khác',
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

/// A single search result card (title, snippet, source badge).
class _SearchResultCard extends StatelessWidget {
  final int index;
  final Map<String, dynamic> result;

  const _SearchResultCard({required this.index, required this.result});

  @override
  Widget build(BuildContext context) {
    final title = (result['title'] as String? ?? '').trim();
    final snippet = (result['snippet'] as String? ?? '').trim();
    final isWeb = result['source'] == 'web';

    return Semantics(
      label: 'Kết quả $index. ${isWeb ? 'Trang web' : 'Tin tức'}. $title. $snippet',
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF141829),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: const Color(0xFF8892B0).withValues(alpha: 0.25),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 28,
                  height: 28,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: (isWeb ? const Color(0xFF00F0FF) : const Color(0xFFFFB300))
                        .withValues(alpha: 0.2),
                    shape: BoxShape.circle,
                  ),
                  child: Text(
                    '$index',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFFFFFFFF),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: (isWeb ? const Color(0xFF00F0FF) : const Color(0xFFFFB300))
                        .withValues(alpha: 0.18),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    isWeb ? 'Trang web' : 'Tin tức',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFFFFFFFF),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            if (title.isNotEmpty) ...[
              Text(
                title,
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFFFFFFFF),
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 6),
            ],
            if (snippet.isNotEmpty)
              Text(
                snippet,
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 14,
                  color: Color(0xFFB6BFD6),
                  height: 1.4,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
