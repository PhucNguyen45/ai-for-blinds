import 'dart:async';
import 'dart:typed_data';

import 'package:camera/camera.dart' show CameraException;
import 'package:flutter/material.dart';

import '../app_services.dart';
import '../capture/capture_coach.dart';
import '../capture/live_guide.dart';
import '../reader/reader_controller.dart';
import '../services/capture_source.dart';
import '../services/earcons.dart';
import '../strings.dart';
import 'ask_screen.dart';
import 'explore.dart';
import 'library_screen.dart';
import 'settings_screen.dart';
import 'theme.dart';
import 'widgets.dart';

enum _Stage { camera, busy, result, error }

/// Màn hình chính. Mở app là vào thẳng đây, camera tràn cả màn hình.
///
/// Ba vùng cố định, không bao giờ đổi chỗ:
/// - góc trên: Cài đặt (trái), Trợ giúp (phải);
/// - giữa: vùng chụp; sau khi chụp, kết quả hiện ngay trong vùng này;
/// - mép dưới: Đọc lại, Hỏi, Thư viện.
///
/// Thao tác: chạm một lần nghe tên, chạm hai lần dùng, rê ngón để dò (xem `explore.dart`).
/// Nút âm lượng: đang đọc thì dừng, còn lại thì chụp ngay.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.services, this.voiceReady = true});

  final AppServices services;
  final bool voiceReady;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver, TickerProviderStateMixin {
  StreamSubscription<String>? _volumeSub;

  /// Người dùng đã rời kết quả để chụp trang mới.
  bool _showCamera = false;

  final _scope = GlobalKey<ExploreScopeState>();

  late final AnimationController _scan = AnimationController(vsync: this, duration: const Duration(milliseconds: 1800));
  late final AnimationController _flash = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 320),
    value: 1,
  );

  AppServices get _s => widget.services;
  ReaderController get _c => _s.controller;

  late final CaptureCoach _coach = CaptureCoach(
    aiming: () =>
        mounted && (_stage == _Stage.camera || _stage == _Stage.error) && (ModalRoute.of(context)?.isCurrent ?? true),
    mayInterrupt: () => !_c.talking && _c.status != ReaderStatus.sending,
    onSignal: _onGuideSignal,
  );

  void _onGuideSignal(GuideSignal signal) {
    final issue = signal.issue;
    if (issue == null) {
      // Khung hình đã ổn: chỉ một âm ngắn kèm rung nhẹ, không nói.
      unawaited(_s.earcons.play(Earcon.focus));
      unawaited(_s.haptics.focus());
    } else {
      unawaited(_c.announce(S.liveHint(issue)));
    }
  }

  /// Theo dõi khung hình khi người dùng bật hướng dẫn chụp.
  void _syncGuide() => _s.capture.watchFrames(_s.settings.captureGuideOn ? _coach.onFrame : null);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _c.addListener(_syncScan);
    _syncGuide();
    _s.capture.open();
    _listenVolumeKeys();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _c.removeListener(_syncScan);
    _volumeSub?.cancel();
    _s.capture.watchFrames(null);
    _s.capture.close();
    _scan.dispose();
    _flash.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Camera phải nhả khi app chạy nền, mở lại khi quay về (chỉ khi màn hình này đang hiện).
    if (state == AppLifecycleState.inactive || state == AppLifecycleState.paused) {
      _s.capture.close();
    } else if (state == AppLifecycleState.resumed && (ModalRoute.of(context)?.isCurrent ?? true)) {
      _s.capture.open();
    }
  }

  void _syncScan() {
    final run = _c.busy && _c.pendingQuestion == null && mounted && !MediaQuery.disableAnimationsOf(context);
    if (run && !_scan.isAnimating) {
      _scan.repeat();
    } else if (!run && _scan.isAnimating) {
      _scan.stop();
    }
  }

  void _listenVolumeKeys() {
    _volumeSub ??= _s.bridge.volumeKeys.listen((_) => _primary());
  }

  void _stopVolumeKeys() {
    // Không await: lệnh huỷ là một lời gọi sang Android, không cần chờ nó xong.
    final sub = _volumeSub;
    _volumeSub = null;
    unawaited(sub?.cancel());
  }

  _Stage get _stage {
    if (_c.busy && _c.pendingQuestion == null) return _Stage.busy;
    if (_showCamera) return _Stage.camera;
    if (_c.status == ReaderStatus.error && _c.errorScope == ReaderController.pageId) return _Stage.error;
    if (_c.last != null) return _Stage.result;
    return _Stage.camera;
  }

  // ---------------------------------------------------------------- hành động

  Future<void> _primary() async {
    _scope.currentState?.clearFocus();
    _s.haptics.capture();
    if (await _c.primaryAction()) await _captureAndDescribe();
  }

  Future<void> _captureAndDescribe() async {
    switch (_s.capture.state.value) {
      case CameraState.denied:
        return _c.fail(S.cameraDenied);
      case CameraState.missing:
        return _c.fail(S.noCamera);
      case CameraState.loading:
      case CameraState.failed:
        return _c.announce(S.cameraNotReady);
      case CameraState.ready:
        break;
    }
    try {
      final bytes = await _s.capture.takePicture();
      if (bytes == null) return _c.announce(S.cameraNotReady);
      if (mounted && !MediaQuery.disableAnimationsOf(context)) _flash.forward(from: 0);
      await _describe(bytes, fromCamera: true);
    } on CameraException {
      await _c.fail(S.cameraNotReady);
    }
  }

  Future<void> _describe(Uint8List bytes, {bool fromCamera = false}) async {
    if (mounted) setState(() => _showCamera = false);
    await _c.describe(bytes, fromCamera: fromCamera);
  }

  Future<void> _stageActivate() async {
    switch (_stage) {
      case _Stage.camera:
        await _primary();
      case _Stage.busy:
        await _c.announce(S.working);
      case _Stage.result:
      case _Stage.error:
        setState(() => _showCamera = true);
        _c.clearError();
        await _c.announce(S.cameraReady);
    }
  }

  Future<void> _pickImage() async {
    if (_c.busy) return _c.announce(S.working);
    final bytes = await _s.capture.pickFromGallery();
    if (bytes == null) return _c.announce(S.pickCancelled);
    await _describe(bytes);
  }

  /// Mở màn hình con: dừng đọc, nhả camera và nút âm lượng (ở màn hình con nút âm lượng chỉnh âm lượng).
  Future<T?> _push<T>(Widget page) async {
    _scope.currentState?.clearFocus();
    await _c.stopSpeaking();
    _stopVolumeKeys();
    await _s.capture.close();
    if (!mounted) return null;
    final result = await Navigator.of(context).push<T>(MaterialPageRoute(builder: (_) => page));
    if (!mounted) return result;
    _syncGuide(); // người hỗ trợ có thể vừa bật hoặc tắt hướng dẫn
    await _s.capture.open();
    _listenVolumeKeys();
    return result;
  }

  Future<void> _openAsk() async {
    final last = _c.last;
    if (last == null) return _c.warn(S.askNeedPage);
    if (!last.canAsk) return _c.warn(S.askCannot);
    await _push<void>(AskScreen(services: _s));
    if (mounted) await _c.announce(S.homeSay);
  }

  Future<void> _openLibrary() async {
    await _push<void>(LibraryScreen(services: _s));
    if (mounted) await _c.announce(S.homeSay);
  }

  Future<void> _openSettings() async {
    final r = await _push<String>(SettingsScreen(services: _s));
    if (!mounted) return;
    if (r == SettingsScreen.pickImage) {
      await _pickImage();
    } else {
      await _c.announce(S.homeSay);
    }
  }

  // ---------------------------------------------------------------- giao diện

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.ink,
      body: ExploreScope(
        key: _scope,
        feedback: _s,
        child: ListenableBuilder(
          listenable: _c,
          builder: (context, _) {
            final stage = _stage;
            return Stack(
              fit: StackFit.expand,
              children: [
                _backdrop(stage),
                const _Scrims(),
                IgnorePointer(
                  child: FadeTransition(
                    opacity: _flash.drive(Tween(begin: 0.85, end: 0.0)),
                    child: const ColoredBox(color: Colors.white),
                  ),
                ),
                SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(8, 4, 8, 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: GlassButton(
                                label: S.settings,
                                spoken: S.settingsSay,
                                icon: Icons.tune_rounded,
                                onActivate: _openSettings,
                              ),
                            ),
                            Expanded(
                              child: GlassButton(
                                label: S.helpLabel,
                                spoken: S.helpSay,
                                icon: Icons.help_rounded,
                                onActivate: () => _c.readText(S.help, id: 'help'),
                              ),
                            ),
                          ],
                        ),
                        if (!widget.voiceReady) _VoiceMissing(onOpen: _s.bridge.openTtsSettings),
                        Expanded(child: _stageTarget(stage)),
                        const SizedBox(height: 6),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 5),
                          child: CaptionBubble(caption: _s.caption),
                        ),
                        const SizedBox(height: 4),
                        SizedBox(
                          height: AppTheme.tileHeight,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Expanded(
                                child: ColorTile(
                                  label: S.repeat,
                                  spoken: S.repeatSay,
                                  icon: Icons.replay_rounded,
                                  color: AppTheme.guide,
                                  onActivate: _c.repeat,
                                ),
                              ),
                              Expanded(
                                child: ColorTile(
                                  label: S.ask,
                                  spoken: S.askSay,
                                  icon: Icons.forum_rounded,
                                  color: AppTheme.ask,
                                  onActivate: _openAsk,
                                ),
                              ),
                              Expanded(
                                child: ColorTile(
                                  label: S.library,
                                  spoken: S.librarySay,
                                  icon: Icons.auto_stories_rounded,
                                  color: AppTheme.lib,
                                  onActivate: _openLibrary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  /// Nền: hình camera trực tiếp, hoặc ảnh vừa chụp khi đang chờ và khi xem kết quả.
  Widget _backdrop(_Stage stage) {
    final img = _c.lastImage;
    if (img != null && stage != _Stage.camera) {
      return Image.memory(
        img,
        fit: BoxFit.cover,
        gaplessPlayback: true,
        cacheWidth: 1080,
        errorBuilder: (_, _, _) => const ColoredBox(color: AppTheme.ink),
      );
    }
    return ValueListenableBuilder<CameraState>(
      valueListenable: _s.capture.state,
      builder: (_, state, _) =>
          state == CameraState.ready ? _s.capture.preview() : const ColoredBox(color: AppTheme.ink),
    );
  }

  Widget _stageTarget(_Stage stage) {
    final (label, spoken, hint) = switch (stage) {
      _Stage.camera => (S.captureLabel, S.captureSay, 'Chụp trang sách. Có thể bấm nút âm lượng.'),
      _Stage.busy => (S.captureLabel, S.busySay, null),
      _Stage.result => (S.resultLabel, S.resultSay, 'Quay lại camera để chụp trang mới.'),
      _Stage.error => (S.stateError, S.errorSay, 'Quay lại camera.'),
    };
    final reduce = MediaQuery.disableAnimationsOf(context);
    return ExploreTarget(
      label: label,
      spoken: spoken,
      hint: hint,
      onActivate: _stageActivate,
      builder: (context, focused) => FocusFrame(
        focused: focused,
        radius: 28,
        child: AnimatedSwitcher(
          duration: reduce ? Duration.zero : const Duration(milliseconds: 280),
          switchInCurve: Curves.easeOutCubic,
          transitionBuilder: (child, anim) => FadeTransition(
            opacity: anim,
            child: SlideTransition(
              position: anim.drive(Tween(begin: const Offset(0, 0.04), end: Offset.zero)),
              child: child,
            ),
          ),
          child: KeyedSubtree(
            key: ValueKey(stage),
            child: switch (stage) {
              _Stage.camera || _Stage.busy => _cameraStage(busy: stage == _Stage.busy),
              _Stage.result => _resultCard(),
              _Stage.error => _errorCard(),
            },
          ),
        ),
      ),
    );
  }

  Widget _cameraStage({required bool busy}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(28),
      child: Stack(
        fit: StackFit.expand,
        children: [
          if (busy) ColoredBox(color: AppTheme.ink.withValues(alpha: 0.35)),
          const Padding(padding: EdgeInsets.all(14), child: PageBrackets()),
          if (busy)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 24),
              child: AnimatedBuilder(
                animation: _scan,
                builder: (_, _) => Align(
                  alignment: Alignment(0, -1 + 2 * Curves.easeInOut.transform(_scan.value)),
                  child: Container(
                    height: 4,
                    decoration: BoxDecoration(
                      color: AppTheme.guide,
                      borderRadius: BorderRadius.circular(2),
                      boxShadow: [
                        BoxShadow(color: AppTheme.guide.withValues(alpha: 0.6), blurRadius: 18, spreadRadius: 2),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          if (!busy)
            ValueListenableBuilder<CameraState>(
              valueListenable: _s.capture.state,
              builder: (_, state, _) => switch (state) {
                CameraState.ready => const SizedBox.shrink(),
                _ => Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 28),
                    child: Text(
                      switch (state) {
                        CameraState.denied => S.cameraDenied,
                        CameraState.missing => S.noCamera,
                        CameraState.loading => S.cameraOpening,
                        _ => S.cameraNotReady,
                      },
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w600, color: AppTheme.paper),
                    ),
                  ),
                ),
              },
            ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.only(bottom: 22, left: 12, right: 12),
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    StatusPill(text: busy ? S.stateSending : S.captureHint),
                    const SizedBox(height: 14),
                    ShutterRing(busy: busy),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _card({required Widget child}) => Container(
    decoration: BoxDecoration(
      color: AppTheme.surface.withValues(alpha: 0.97),
      borderRadius: BorderRadius.circular(28),
      border: Border.all(color: AppTheme.line, width: 1.5),
    ),
    padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
    child: child,
  );

  Widget _resultCard() {
    final last = _c.last!;
    final kind = S.kindName(last.pageType);
    final reading = _c.readingId == ReaderController.pageId && _c.sentenceIndex >= 0;
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              _Thumb(bytes: _c.lastImage),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      S.resultTitle,
                      style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800, color: AppTheme.paper),
                    ),
                    if (kind != null) ...[const SizedBox(height: 4), Tag(text: kind)],
                  ],
                ),
              ),
              AnimatedOpacity(
                opacity: reading ? 1 : 0,
                duration: const Duration(milliseconds: 200),
                child: const Icon(Icons.graphic_eq_rounded, size: 30, color: AppTheme.guide),
              ),
            ],
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Divider(height: 1, color: AppTheme.line),
          ),
          Expanded(
            child: ReadingText(
              sentences: _c.pageSentences,
              active: _c.readingId == ReaderController.pageId ? _c.sentenceIndex : -1,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            S.newPageHint,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppTheme.mute),
          ),
        ],
      ),
    );
  }

  Widget _errorCard() {
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Row(
            children: [
              Icon(Icons.error_rounded, size: 34, color: AppTheme.danger),
              SizedBox(width: 10),
              Text(
                S.stateError,
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.danger),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: SingleChildScrollView(
              child: Text(_c.errorText, style: const TextStyle(fontSize: 21, height: 1.45, color: AppTheme.paper)),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            S.retryHint,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppTheme.mute),
          ),
        ],
      ),
    );
  }
}

/// Ảnh nhỏ của trang vừa chụp cạnh kết quả (cho người hỗ trợ đối chiếu).
class _Thumb extends StatelessWidget {
  const _Thumb({required this.bytes});
  final Uint8List? bytes;

  @override
  Widget build(BuildContext context) {
    final b = bytes;
    return Container(
      width: 58,
      height: 58,
      decoration: BoxDecoration(
        color: AppTheme.surfaceHigh,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.guide, width: 2),
      ),
      clipBehavior: Clip.antiAlias,
      child: b == null
          ? const Icon(Icons.menu_book_rounded, color: AppTheme.guide)
          : Image.memory(
              b,
              fit: BoxFit.cover,
              cacheWidth: 180,
              errorBuilder: (_, _, _) => const Icon(Icons.menu_book_rounded, color: AppTheme.guide),
            ),
    );
  }
}

/// Lớp tối trên và dưới để chữ, nút luôn rõ trên hình camera.
class _Scrims extends StatelessWidget {
  const _Scrims();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Stack(
        children: [
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: 190,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [AppTheme.ink.withValues(alpha: 0.9), AppTheme.ink.withValues(alpha: 0)],
                ),
              ),
            ),
          ),
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            height: 330,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  stops: const [0, 0.42, 1],
                  colors: [AppTheme.ink.withValues(alpha: 0), AppTheme.ink.withValues(alpha: 0.94), AppTheme.ink],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _VoiceMissing extends StatelessWidget {
  const _VoiceMissing({required this.onOpen});
  final Future<void> Function() onOpen;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(5, 6, 5, 0),
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: AppTheme.ink.withValues(alpha: 0.9),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppTheme.danger, width: 2),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(S.voiceMissingShown, style: TextStyle(fontSize: 16, height: 1.35, color: AppTheme.danger)),
            const SizedBox(height: 6),
            RowButton(
              title: S.openTtsSettings,
              spoken: S.openTtsSettings,
              icon: Icons.record_voice_over_rounded,
              accent: AppTheme.danger,
              onActivate: onOpen,
            ),
          ],
        ),
      ),
    );
  }
}
