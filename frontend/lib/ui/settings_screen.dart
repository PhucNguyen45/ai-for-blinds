import 'dart:async';

import 'package:flutter/material.dart';

import '../api/models.dart';
import '../app_services.dart';
import '../reader/reader_controller.dart';
import '../services/settings_store.dart';
import '../strings.dart';
import 'explore.dart';
import 'theme.dart';
import 'widgets.dart';

/// Cài đặt cho học sinh: năm mục lớn, dùng bằng chạm nghe / chạm hai lần, không cần cuộn.
/// Mục nào đổi giá trị thì đọc ngay giá trị mới (tốc độ đọc thì nghe thử luôn ở tốc độ mới).
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key, required this.services});
  final AppServices services;

  /// Kết quả trả về màn hình chính khi chọn "Đọc ảnh có sẵn".
  static const pickImage = 'pick';

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  SettingsStore get _s => widget.services.settings;
  ReaderController get _c => widget.services.controller;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _c.announce(S.settingsOpen));
  }

  String _onOff(bool v) => v ? S.on : S.off;

  Future<void> _cycleRate() async {
    final next = _s.nextRatePreset;
    await _s.setSpeechRate(next.value);
    await widget.services.speaker.setRate(next.value);
    await _c.announce('${S.speechRate}: ${next.name}. ${S.tryVoiceSentence}');
  }

  Future<void> _toggleSound() async {
    await _s.setSoundOn(!_s.soundOn);
    await _c.announce('${S.sound}: ${_onOff(_s.soundOn)}.');
  }

  Future<void> _toggleVibrate() async {
    await _s.setVibrateOn(!_s.vibrateOn);
    await widget.services.haptics.activate();
    await _c.announce('${S.vibrate}: ${_onOff(_s.vibrateOn)}.');
  }

  Future<void> _openAdvanced() async {
    await _c.stopSpeaking();
    if (!mounted) return;
    await Navigator.of(
      context,
    ).push(MaterialPageRoute<void>(builder: (_) => AdvancedSettingsScreen(services: widget.services)));
    if (mounted) await _c.announce(S.settingsOpen);
  }

  Future<void> _back([String? result]) async {
    await _c.stopSpeaking();
    if (mounted) Navigator.of(context).pop(result);
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
              listenable: _s,
              builder: (context, _) {
                final rows = <Widget>[
                  RowButton(
                    title: S.speechRate,
                    value: _s.ratePreset.name,
                    spoken: '${S.speechRate}: ${_s.ratePreset.name}. ${S.changeHint}',
                    icon: Icons.speed_rounded,
                    accent: AppTheme.guide,
                    onActivate: () => unawaited(_cycleRate()),
                  ),
                  RowButton(
                    title: S.sound,
                    value: _onOff(_s.soundOn),
                    spoken: '${S.sound}: ${_onOff(_s.soundOn)}. ${S.changeHint}',
                    icon: Icons.music_note_rounded,
                    accent: AppTheme.guide,
                    onActivate: () => unawaited(_toggleSound()),
                  ),
                  RowButton(
                    title: S.vibrate,
                    value: _onOff(_s.vibrateOn),
                    spoken: '${S.vibrate}: ${_onOff(_s.vibrateOn)}. ${S.changeHint}',
                    icon: Icons.vibration_rounded,
                    accent: AppTheme.guide,
                    onActivate: () => unawaited(_toggleVibrate()),
                  ),
                  RowButton(
                    title: S.pickImage,
                    subtitle: S.pickImageSub,
                    spoken: '${S.pickImage}. ${S.pickImageSub}. ${S.openHint}',
                    icon: Icons.photo_library_rounded,
                    accent: AppTheme.ask,
                    onActivate: () => unawaited(_back(SettingsScreen.pickImage)),
                  ),
                  RowButton(
                    title: S.advanced,
                    subtitle: S.advancedSub,
                    spoken: '${S.advanced}. ${S.advancedSub}. ${S.openHint}',
                    icon: Icons.admin_panel_settings_rounded,
                    accent: AppTheme.lib,
                    onActivate: () => unawaited(_openAdvanced()),
                  ),
                ];
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    ScreenHeader(title: S.settings, intro: S.settingsOpen, onIntro: () => _c.announce(S.settingsOpen)),
                    const SizedBox(height: 4),
                    // Năm hàng chia đều chiều cao còn lại, không cần cuộn (cuộn khó khi không nhìn).
                    for (final r in rows) Expanded(child: r),
                    BackBar(onActivate: () => unawaited(_back())),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}

/// Cài đặt cho người hỗ trợ (giáo viên, phụ huynh, nhóm thử nghiệm): biểu mẫu thường,
/// dùng bằng mắt hoặc với TalkBack. Riêng dải Quay lại vẫn chạm nghe / chạm hai lần như mọi màn hình.
class AdvancedSettingsScreen extends StatefulWidget {
  const AdvancedSettingsScreen({super.key, required this.services});
  final AppServices services;

  @override
  State<AdvancedSettingsScreen> createState() => _AdvancedSettingsScreenState();
}

class _AdvancedSettingsScreenState extends State<AdvancedSettingsScreen> {
  late final TextEditingController _url = TextEditingController(text: _s.serverUrl);
  late double _rate = _s.speechRate.clamp(0.3, 1.0);
  bool _checking = false;

  SettingsStore get _s => widget.services.settings;
  ReaderController get _c => widget.services.controller;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _c.announce(S.advancedOpen));
  }

  @override
  void dispose() {
    _url.dispose();
    super.dispose();
  }

  Future<void> _saveUrl() async {
    if (_url.text.trim() != _s.serverUrl) await _s.setServerUrl(_url.text);
    _url.text = _s.serverUrl;
  }

  Future<void> _check() async {
    setState(() => _checking = true);
    await _saveUrl();
    final result = await _s.api.health();
    if (!mounted) return;
    setState(() => _checking = false);
    final spoken = switch (result) {
      ApiOk(:final value) => value.isMock ? '${S.serverOkPrefix} ${S.serverModeMock}' : S.serverOkPrefix,
      ApiFail(:final message) => message,
    };
    await _c.announce(spoken);
  }

  Future<void> _rateChanged(double v) async {
    await _s.setSpeechRate(v);
    await widget.services.speaker.setRate(v);
    await _c.announce(S.tryVoiceSentence);
  }

  Future<void> _back() async {
    await _saveUrl();
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
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ScreenHeader(title: S.advancedTitle, intro: S.advancedOpen, onIntro: () => _c.announce(S.advancedOpen)),
                Expanded(
                  child: ListenableBuilder(
                    listenable: _s,
                    builder: (context, _) => ListView(
                      padding: const EdgeInsets.fromLTRB(6, 8, 6, 16),
                      children: [
                        _label(S.serverUrl),
                        TextField(
                          controller: _url,
                          keyboardType: TextInputType.url,
                          autocorrect: false,
                          enabled: !_s.demoMode,
                          style: const TextStyle(fontSize: 20),
                          decoration: const InputDecoration(
                            helperText: S.serverUrlHint,
                            helperMaxLines: 3,
                            helperStyle: TextStyle(fontSize: 15, color: AppTheme.mute),
                          ),
                          onSubmitted: (_) => _saveUrl(),
                        ),
                        const SizedBox(height: 10),
                        _button(
                          _checking ? 'Đang kiểm tra…' : S.checkServer,
                          Icons.wifi_tethering_rounded,
                          _checking ? null : _check,
                        ),
                        const SizedBox(height: 24),
                        _label('${S.speechRateFine}: ${(_rate * 100).round()}'),
                        Semantics(
                          label: S.speechRateFine,
                          child: Slider(
                            value: _rate,
                            min: 0.3,
                            max: 1.0,
                            divisions: 14,
                            label: '${(_rate * 100).round()}',
                            onChanged: (v) => setState(() => _rate = v),
                            onChangeEnd: _rateChanged,
                          ),
                        ),
                        _button(S.tryVoice, Icons.volume_up_rounded, () => _c.announce(S.tryVoiceSentence)),
                        const SizedBox(height: 24),
                        _label(S.pageType),
                        DropdownButtonFormField<String>(
                          initialValue: _s.pageType,
                          isExpanded: true,
                          itemHeight: AppTheme.minTouch,
                          style: const TextStyle(fontFamily: AppTheme.font, fontSize: 20, color: AppTheme.paper),
                          dropdownColor: AppTheme.surface,
                          items: [
                            for (final e in S.pageTypes.entries) DropdownMenuItem(value: e.key, child: Text(e.value)),
                          ],
                          onChanged: (v) async {
                            if (v == null) return;
                            await _s.setPageType(v);
                            await _c.announce('${S.pageType}: ${S.pageTypes[v]}. ${S.saved}');
                          },
                        ),
                        const SizedBox(height: 20),
                        MergeSemantics(
                          child: SwitchListTile(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                            minTileHeight: AppTheme.minTouch,
                            title: const Text(S.demoMode, style: TextStyle(fontSize: 21, fontWeight: FontWeight.w700)),
                            subtitle: const Text(S.demoModeHint, style: TextStyle(fontSize: 15, color: AppTheme.mute)),
                            value: _s.demoMode,
                            onChanged: (v) async {
                              await _s.setDemoMode(v);
                              await _c.announce('${S.demoMode} ${v ? 'bật' : 'tắt'}.');
                            },
                          ),
                        ),
                        const SizedBox(height: 16),
                        _button(
                          S.openTtsSettings,
                          Icons.record_voice_over_rounded,
                          widget.services.bridge.openTtsSettings,
                        ),
                        const SizedBox(height: 10),
                        _button(S.replayTutorial, Icons.school_rounded, () => _c.readText(S.tutorial, id: 'help')),
                      ],
                    ),
                  ),
                ),
                BackBar(onActivate: () => unawaited(_back())),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _label(String text) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Text(text, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
  );

  /// Nút thường (chạm là dùng): màn hình này dành cho người nhìn được hoặc dùng TalkBack.
  Widget _button(String label, IconData icon, VoidCallback? onPressed) => SizedBox(
    height: AppTheme.minTouch,
    child: FilledButton.tonalIcon(
      onPressed: onPressed,
      icon: Icon(icon, size: 26),
      label: Text(label, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
      style: FilledButton.styleFrom(
        backgroundColor: AppTheme.surfaceHigh,
        foregroundColor: AppTheme.paper,
        disabledBackgroundColor: AppTheme.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: AppTheme.line, width: 1.5),
        ),
      ),
    ),
  );
}
