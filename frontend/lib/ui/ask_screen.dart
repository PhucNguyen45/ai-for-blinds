import 'dart:async';

import 'package:flutter/material.dart';

import '../app_services.dart';
import '../reader/reader_controller.dart';
import '../services/earcons.dart';
import '../services/speech_input.dart';
import '../strings.dart';
import 'explore.dart';
import 'theme.dart';
import 'widgets.dart';

/// Hỏi tiếp về trang vừa chụp BẰNG GIỌNG NÓI (học theo "Ask more" của Be My AI).
///
/// - Bấm nút âm lượng, hoặc chạm hai lần nút "Nói câu hỏi" (ngay trên Quay lại), rồi nói.
/// - Nhận giọng nói bằng dịch vụ có sẵn của Android, tiếng Việt (services/speech_input.dart).
/// - Đang nghe mà chạm bất kỳ đâu: dừng nghe (app không đọc tên nút lúc này để giọng app không lọt vào micro).
/// - Máy không có dịch vụ nhận giọng nói: hiện ba câu hỏi gợi ý thay cho nút nói.
/// Câu hỏi gửi lên `/v1/ask` kèm lịch sử hỏi đáp, hoặc trả lời mẫu khi bật chế độ demo.
class AskScreen extends StatefulWidget {
  const AskScreen({super.key, required this.services});
  final AppServices services;

  /// Nghe tối đa bao lâu thì tự dừng thu âm (một câu hỏi thường dưới 10 giây).
  static const nghiToiDa = Duration(seconds: 12);

  /// Sau khi dừng thu, chờ kết quả thêm bao lâu thì bỏ (mạng yếu).
  static const choKetQua = Duration(seconds: 8);

  @override
  State<AskScreen> createState() => _AskScreenState();
}

class _AskScreenState extends State<AskScreen> with SingleTickerProviderStateMixin implements ExploreFeedback {
  final _scope = GlobalKey<ExploreScopeState>();
  // Tạo ngay trong initState (không để lười): dispose() không được là nơi tạo lần đầu.
  late final AnimationController _pulse;

  /// null: đang kiểm tra máy có nhận giọng nói không.
  bool? _sttOk;
  bool _listening = false;
  String _partial = '';
  StreamSubscription<String>? _partialSub;
  StreamSubscription<String>? _volumeSub;

  AppServices get _s => widget.services;
  ReaderController get _c => _s.controller;
  SpeechInput get _stt => _s.speechInput;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(vsync: this, duration: const Duration(milliseconds: 1100));
    _init();
  }

  Future<void> _init() async {
    final ok = await _stt.available();
    if (!mounted) return;
    setState(() => _sttOk = ok);
    if (ok) {
      _partialSub = _stt.partials.listen((t) {
        if (_listening && mounted) setState(() => _partial = t);
      });
      _volumeSub = _s.bridge.volumeKeys.listen((_) => _toggle());
    }
    await _c.announce(ok ? S.askOpen : S.askOpenNoStt);
  }

  @override
  void dispose() {
    unawaited(_partialSub?.cancel());
    unawaited(_volumeSub?.cancel()); // không await: lời gọi sang Android
    if (_listening) unawaited(_stt.cancel());
    _pulse.dispose();
    super.dispose();
  }

  // Phản hồi chạm của màn hình này: đang nghe thì chạm = dừng nghe, không nói gì.
  @override
  void onFocus(String spoken) {
    if (_listening) {
      _scope.currentState?.clearFocus();
      unawaited(_stt.stop());
      return;
    }
    _s.onFocus(spoken);
  }

  @override
  void onActivate() {
    if (!_listening) _s.onActivate();
  }

  Future<void> _toggle() async {
    if (_listening) return _stt.stop();
    if (_c.busy) return _c.announce(S.working);
    _scope.currentState?.clearFocus();
    // Nói xong lời mời rồi mới mở micro, để micro không thu giọng của app.
    await _c.announce(S.sttPrompt);
    if (!mounted) return;
    unawaited(_s.earcons.play(Earcon.activate));
    unawaited(_s.haptics.activate());
    setState(() {
      _listening = true;
      _partial = '';
    });
    if (!MediaQuery.disableAnimationsOf(context)) _pulse.repeat(reverse: true);
    // Chốt chặn: dịch vụ nhận giọng có thể chờ mạng mãi không trả lời (đã gặp trên máy ảo).
    // Sau [nghiToiDa] tự dừng thu âm (vẫn lấy phần đã nghe); thêm [choKetQua] nữa thì huỷ hẳn và báo lỗi mạng.
    var hetGio = false;
    final dung = Timer(AskScreen.nghiToiDa, () {
      if (_listening) unawaited(_stt.stop());
    });
    final huy = Timer(AskScreen.nghiToiDa + AskScreen.choKetQua, () {
      if (_listening) {
        hetGio = true;
        unawaited(_stt.cancel());
      }
    });
    final r = await _stt.listen();
    dung.cancel();
    huy.cancel();
    if (!mounted) return;
    _pulse.stop();
    setState(() => _listening = false);
    switch (r) {
      case SttText(:final text):
        await _c.ask(text);
      case SttFail(:final message):
        await _c.warn(message);
      case SttCancelled():
        if (hetGio) await _c.warn(S.sttNetwork);
    }
  }

  Future<void> _back() async {
    if (_listening) await _stt.cancel();
    await _c.stopSpeaking();
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final noStt = _sttOk == false;
    return Scaffold(
      body: ExploreScope(
        key: _scope,
        feedback: this,
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
                    intro: noStt ? S.askOpenNoStt : S.askOpen,
                    onIntro: () => _c.announce(noStt ? S.askOpenNoStt : S.askOpen),
                    trailing: _thumb(),
                  ),
                  Expanded(child: _answerTarget(noStt)),
                  if (noStt)
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
                      )
                  else
                    _micTile(),
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

  Widget _micTile() {
    final on = _listening;
    final color = on ? AppTheme.guide : AppTheme.ask;
    return ExploreTarget(
      label: on ? S.micStop : S.mic,
      spoken: on ? S.micStopSay : S.micSay,
      hint: on ? null : 'Có thể bấm nút âm lượng.',
      onActivate: () => unawaited(_toggle()),
      builder: (context, focused) => FocusFrame(
        focused: focused,
        child: Container(
          height: 122,
          decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(AppTheme.radius)),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
          child: FittedBox(
            fit: BoxFit.scaleDown,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(color: AppTheme.ink.withValues(alpha: 0.12), shape: BoxShape.circle),
                  child: Icon(on ? Icons.stop_rounded : Icons.mic_rounded, size: 38, color: AppTheme.ink),
                ),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      on ? S.listeningShown : S.mic,
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppTheme.ink),
                    ),
                    Text(
                      on ? 'Chạm để dừng' : 'hoặc bấm nút âm lượng',
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: AppTheme.ink),
                    ),
                  ],
                ),
              ],
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

  Widget _answerTarget(bool noStt) {
    final turns = _c.turns;
    final spoken = turns.isEmpty ? (noStt ? S.askEmptyNoStt : S.askEmpty) : S.answerSay;
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
            border: Border.all(color: _listening ? AppTheme.guide : AppTheme.line, width: _listening ? 2.5 : 1.5),
          ),
          padding: const EdgeInsets.all(14),
          child: _listening ? _listeningBody() : _answerBody(noStt),
        ),
      ),
    );
  }

  Widget _listeningBody() {
    return Center(
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ScaleTransition(
              scale: Tween(begin: 0.9, end: 1.08).animate(CurvedAnimation(parent: _pulse, curve: Curves.easeInOut)),
              child: Container(
                width: 96,
                height: 96,
                decoration: BoxDecoration(
                  color: AppTheme.guide,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(color: AppTheme.guide.withValues(alpha: 0.45), blurRadius: 28, spreadRadius: 4),
                  ],
                ),
                child: const Icon(Icons.mic_rounded, size: 52, color: AppTheme.ink),
              ),
            ),
            const SizedBox(height: 18),
            Text(
              _partial.isEmpty ? S.listeningShown : '“$_partial”',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: _partial.isEmpty ? 22 : 21,
                height: 1.4,
                fontWeight: FontWeight.w700,
                color: _partial.isEmpty ? AppTheme.guide : AppTheme.paper,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _answerBody(bool noStt) {
    final pending = _c.pendingQuestion;
    final failed = _c.status == ReaderStatus.error && _c.errorScope == ReaderController.answerId;
    final turns = _c.turns;
    final question = pending ?? (turns.isEmpty ? null : turns.last.question);

    if (question == null && !failed) {
      return Center(
        child: Text(
          noStt ? S.askEmptyShownNoStt : S.askEmptyShown,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 19, height: 1.4, fontWeight: FontWeight.w600, color: AppTheme.mute),
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
