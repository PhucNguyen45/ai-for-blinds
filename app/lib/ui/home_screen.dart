import 'dart:async';

import 'package:camera/camera.dart' show CameraException;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../reader/reader_controller.dart';
import '../services/capture_source.dart';
import '../services/platform_bridge.dart';
import '../services/settings_store.dart';
import '../services/speech.dart';
import '../strings.dart';
import 'big_button.dart';
import 'settings_screen.dart';
import 'theme.dart';

/// Màn hình chính: gần như cả màn hình là một nút chụp.
///
/// Thao tác:
/// - chạm vùng camera (TalkBack: chạm hai lần) hoặc bấm nút âm lượng → chụp và đọc;
/// - đang đọc mà chạm lại → dừng đọc;
/// - ba nút lớn ở cuối: Đọc lại, Chọn ảnh, Cài đặt.
class HomeScreen extends StatefulWidget {
  const HomeScreen({
    super.key,
    required this.controller,
    required this.settings,
    required this.capture,
    required this.bridge,
    required this.speaker,
    this.voiceReady = true,
  });

  final ReaderController controller;
  final SettingsStore settings;
  final CaptureSource capture;
  final PlatformBridge bridge;
  final Speaker speaker;
  final bool voiceReady;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {
  StreamSubscription<String>? _volumeSub;

  ReaderController get _c => widget.controller;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    widget.capture.open();
    _listenVolumeKeys();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _volumeSub?.cancel();
    widget.capture.close();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Camera phải nhả khi app chạy nền, mở lại khi quay về.
    if (state == AppLifecycleState.inactive || state == AppLifecycleState.paused) {
      widget.capture.close();
    } else if (state == AppLifecycleState.resumed) {
      widget.capture.open();
    }
  }

  void _listenVolumeKeys() {
    _volumeSub ??= widget.bridge.volumeKeys.listen((_) => _primary());
  }

  void _stopVolumeKeys() {
    // Không await: lệnh huỷ là một lời gọi sang Android, không cần chờ nó xong.
    final sub = _volumeSub;
    _volumeSub = null;
    unawaited(sub?.cancel());
  }

  Future<void> _primary() async {
    HapticFeedback.heavyImpact();
    if (await _c.primaryAction()) await _captureAndDescribe();
  }

  Future<void> _captureAndDescribe() async {
    switch (widget.capture.state.value) {
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
      final bytes = await widget.capture.takePicture();
      if (bytes == null) return _c.announce(S.cameraNotReady);
      await _c.describe(bytes);
    } on CameraException {
      await _c.fail(S.cameraNotReady);
    }
  }

  Future<void> _pickImage() async {
    if (_c.busy) return _c.announce(S.working);
    final bytes = await widget.capture.pickFromGallery();
    if (bytes == null) return _c.announce(S.pickCancelled);
    await _c.describe(bytes);
  }

  Future<void> _openSettings() async {
    await _c.stopSpeaking();
    _stopVolumeKeys(); // ở Cài đặt, nút âm lượng chỉnh âm lượng như bình thường
    await widget.capture.close();
    if (!mounted) return;
    await Navigator.of(context).push(MaterialPageRoute<void>(
      builder: (_) => SettingsScreen(settings: widget.settings, speaker: widget.speaker, bridge: widget.bridge),
    ));
    if (!mounted) return;
    await widget.capture.open();
    _listenVolumeKeys();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (!widget.voiceReady) _VoiceMissingBanner(onOpen: widget.bridge.openTtsSettings),
              Expanded(flex: 5, child: _captureArea()),
              const SizedBox(height: 12),
              Expanded(flex: 3, child: _textPanel()),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: BigButton(
                        label: S.repeat, hint: S.repeatHint, icon: Icons.replay, onPressed: _c.repeat, height: 88),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: BigButton(
                        label: S.pickImage, hint: S.pickImageHint, icon: Icons.photo, onPressed: _pickImage, height: 88),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: BigButton(
                        label: S.settings,
                        hint: S.settingsHint,
                        icon: Icons.settings,
                        onPressed: _openSettings,
                        height: 88),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _captureArea() {
    return Semantics(
      button: true,
      label: S.captureLabel,
      excludeSemantics: true,
      onTap: _primary,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: _primary,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: DecoratedBox(
            decoration: BoxDecoration(
              border: Border.all(color: AppTheme.accent, width: 3),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Stack(
              fit: StackFit.expand,
              children: [
                ValueListenableBuilder<CameraState>(
                  valueListenable: widget.capture.state,
                  builder: (_, state, _) => state == CameraState.ready
                      ? widget.capture.preview()
                      : Center(
                          child: Text(
                            switch (state) {
                              CameraState.denied => S.cameraDenied,
                              CameraState.missing => S.noCamera,
                              _ => S.cameraNotReady,
                            },
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontSize: 22, color: AppTheme.foreground),
                          ),
                        ),
                ),
                Align(alignment: Alignment.bottomCenter, child: _statusPill()),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _statusPill() {
    return ListenableBuilder(
      listenable: _c,
      builder: (_, _) {
        final (text, color) = switch (_c.status) {
          ReaderStatus.idle => (S.captureVisual, AppTheme.accent),
          ReaderStatus.sending => (S.stateSending, AppTheme.accent),
          ReaderStatus.speaking => (S.stateSpeaking, AppTheme.foreground),
          ReaderStatus.error => (S.stateError, AppTheme.danger),
        };
        return Container(
          margin: const EdgeInsets.all(12),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.black,
            borderRadius: BorderRadius.circular(32),
            border: Border.all(color: color, width: 3),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (_c.status == ReaderStatus.sending) ...[
                const SizedBox(
                    width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 3, color: AppTheme.accent)),
                const SizedBox(width: 12),
              ],
              Flexible(
                child: Text(text,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: color)),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _textPanel() {
    return ListenableBuilder(
      listenable: _c,
      builder: (_, _) => DecoratedBox(
        decoration: BoxDecoration(
          border: Border.all(color: AppTheme.foreground, width: 2),
          borderRadius: BorderRadius.circular(16),
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Text(
            _c.shownText.isEmpty ? S.greeting : _c.shownText,
            style: TextStyle(
              fontSize: 22,
              height: 1.45,
              color: _c.status == ReaderStatus.error ? AppTheme.danger : AppTheme.foreground,
            ),
          ),
        ),
      ),
    );
  }
}

class _VoiceMissingBanner extends StatelessWidget {
  const _VoiceMissingBanner({required this.onOpen});
  final Future<void> Function() onOpen;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(S.voiceMissingShown, style: TextStyle(fontSize: 20, color: AppTheme.danger)),
          const SizedBox(height: 8),
          BigButton(label: S.openTtsSettings, icon: Icons.record_voice_over, onPressed: onOpen),
        ],
      ),
    );
  }
}
