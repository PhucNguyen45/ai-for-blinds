import 'dart:async';

import 'package:flutter/material.dart';

import '../app_services.dart';
import '../reader/reader_controller.dart';
import '../strings.dart';
import 'explore.dart';
import 'theme.dart';
import 'widgets.dart';

/// Hỏi tiếp về trang vừa chụp, dạng hội thoại (học theo "Ask more" của Be My AI).
///
/// Chưa có nhận dạng giọng nói (phần của Mảng A), nên hiện ba câu hỏi gợi ý;
/// câu hỏi gửi thật lên `/v1/ask` kèm lịch sử, hoặc trả lời mẫu khi bật chế độ demo.
class AskScreen extends StatefulWidget {
  const AskScreen({super.key, required this.services});
  final AppServices services;

  @override
  State<AskScreen> createState() => _AskScreenState();
}

class _AskScreenState extends State<AskScreen> {
  ReaderController get _c => widget.services.controller;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _c.announce(S.askOpen));
  }

  Future<void> _back() async {
    await _c.stopSpeaking();
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ExploreScope(
        feedback: widget.services,
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 6, 8, 8),
            child: ListenableBuilder(
              listenable: _c,
              builder: (context, _) => Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  ScreenHeader(
                    title: S.askTitle,
                    intro: S.askOpen,
                    onIntro: () => _c.announce(S.askOpen),
                    trailing: _thumb(),
                  ),
                  Expanded(child: _answerTarget()),
                  for (final q in S.askSuggestions)
                    SizedBox(
                      height: 84,
                      child: RowButton(
                        title: q,
                        spoken: '$q. Chạm hai lần để hỏi.',
                        icon: Icons.chat_bubble_rounded,
                        accent: AppTheme.ask,
                        onActivate: () => unawaited(_c.ask(q)),
                      ),
                    ),
                  const SizedBox(height: 2),
                  BackBar(onActivate: _back),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget? _thumb() {
    final b = _c.lastImage;
    if (b == null) return null;
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Image.memory(
        b,
        width: 52,
        height: 52,
        fit: BoxFit.cover,
        cacheWidth: 160,
        errorBuilder: (_, _, _) => const SizedBox(width: 52, height: 52),
      ),
    );
  }

  Widget _answerTarget() {
    final turns = _c.turns;
    final spoken = turns.isEmpty ? S.askEmpty : S.answerSay;
    return ExploreTarget(
      label: S.answerLabel,
      spoken: spoken,
      onActivate: _c.repeatAnswer,
      builder: (context, focused) => FocusFrame(
        focused: focused,
        radius: 26,
        child: Container(
          decoration: BoxDecoration(
            color: AppTheme.surface,
            borderRadius: BorderRadius.circular(26),
            border: Border.all(color: AppTheme.line, width: 1.5),
          ),
          padding: const EdgeInsets.all(14),
          child: _answerBody(),
        ),
      ),
    );
  }

  Widget _answerBody() {
    final pending = _c.pendingQuestion;
    final failed = _c.status == ReaderStatus.error && _c.errorScope == ReaderController.answerId;
    final turns = _c.turns;
    final question = pending ?? (turns.isEmpty ? null : turns.last.question);

    if (question == null && !failed) {
      return const Center(
        child: Text(
          S.askEmptyShown,
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 19, height: 1.4, fontWeight: FontWeight.w600, color: AppTheme.mute),
        ),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (question != null)
          Flexible(
            child: Align(
              alignment: Alignment.topRight,
              child: Container(
                clipBehavior: Clip.hardEdge,
                margin: const EdgeInsets.only(left: 36, bottom: 12),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: const BoxDecoration(
                  color: AppTheme.ask,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(18),
                    topRight: Radius.circular(18),
                    bottomLeft: Radius.circular(18),
                    bottomRight: Radius.circular(4),
                  ),
                ),
                child: Text(
                  question,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.ink),
                ),
              ),
            ),
          ),
        Expanded(
          flex: 2,
          child: pending != null
              ? const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 26,
                      height: 26,
                      child: CircularProgressIndicator(strokeWidth: 3, color: AppTheme.guide),
                    ),
                    SizedBox(width: 12),
                    Text(
                      S.stateAsking,
                      style: TextStyle(fontSize: 19, fontWeight: FontWeight.w700, color: AppTheme.guide),
                    ),
                  ],
                )
              : failed
              ? SingleChildScrollView(
                  child: Text(_c.errorText, style: const TextStyle(fontSize: 20, height: 1.45, color: AppTheme.danger)),
                )
              : ReadingText(
                  sentences: splitSentences(turns.last.answer),
                  active: _c.readingId == ReaderController.answerId ? _c.sentenceIndex : -1,
                  fontSize: 21,
                ),
        ),
      ],
    );
  }
}
