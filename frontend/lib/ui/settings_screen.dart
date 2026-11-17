import 'package:flutter/material.dart';

import '../api/models.dart';
import '../services/platform_bridge.dart';
import '../services/settings_store.dart';
import '../services/speech.dart';
import '../strings.dart';
import 'big_button.dart';
import 'theme.dart';

/// Cài đặt: địa chỉ máy chủ, tốc độ đọc, loại trang, chế độ demo.
/// Mọi kết quả (kết nối được hay không, đã lưu) đều được đọc thành tiếng.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key, required this.settings, required this.speaker, required this.bridge});

  final SettingsStore settings;
  final Speaker speaker;
  final PlatformBridge bridge;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _url = TextEditingController(text: widget.settings.serverUrl);
  late double _rate = widget.settings.speechRate;
  bool _checking = false;

  SettingsStore get _s => widget.settings;

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
    await widget.speaker.speak(spoken);
  }

  Future<void> _rateChanged(double v) async {
    await _s.setSpeechRate(v);
    await widget.speaker.setRate(v);
    await widget.speaker.speak(S.tryVoiceSentence);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text(S.settings)),
      body: ListenableBuilder(
        listenable: _s,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _label(S.serverUrl),
            TextField(
              controller: _url,
              keyboardType: TextInputType.url,
              autocorrect: false,
              enabled: !_s.demoMode,
              style: const TextStyle(fontSize: 22),
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                helperText: S.serverUrlHint,
                helperMaxLines: 3,
                helperStyle: TextStyle(fontSize: 16, color: AppTheme.foreground),
              ),
              onSubmitted: (_) => _saveUrl(),
            ),
            const SizedBox(height: 12),
            BigButton(
              label: _checking ? 'Đang kiểm tra…' : S.checkServer,
              icon: Icons.wifi_tethering,
              onPressed: _checking ? null : _check,
            ),
            const SizedBox(height: 28),
            _label('${S.speechRate}: ${(_rate * 100).round()}'),
            Semantics(
              label: S.speechRate,
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
            BigButton(
              label: S.tryVoice,
              icon: Icons.volume_up,
              onPressed: () => widget.speaker.speak(S.tryVoiceSentence),
            ),
            const SizedBox(height: 28),
            _label(S.pageType),
            DropdownButtonFormField<String>(
              initialValue: _s.pageType,
              isExpanded: true,
              itemHeight: AppTheme.minTouch,
              style: const TextStyle(fontSize: 22, color: AppTheme.foreground),
              dropdownColor: Colors.black,
              decoration: const InputDecoration(border: OutlineInputBorder()),
              items: [
                for (final e in S.pageTypes.entries) DropdownMenuItem(value: e.key, child: Text(e.value)),
              ],
              onChanged: (v) async {
                if (v == null) return;
                await _s.setPageType(v);
                await widget.speaker.speak('${S.pageType}: ${S.pageTypes[v]}. ${S.saved}');
              },
            ),
            const SizedBox(height: 28),
            MergeSemantics(
              child: SwitchListTile(
                contentPadding: EdgeInsets.zero,
                minTileHeight: AppTheme.minTouch,
                title: const Text(S.demoMode, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
                subtitle: const Text(S.demoModeHint, style: TextStyle(fontSize: 18)),
                value: _s.demoMode,
                onChanged: (v) async {
                  await _s.setDemoMode(v);
                  await widget.speaker.speak('${S.demoMode} ${v ? 'bật' : 'tắt'}.');
                },
              ),
            ),
            const SizedBox(height: 28),
            BigButton(label: S.openTtsSettings, icon: Icons.record_voice_over, onPressed: widget.bridge.openTtsSettings),
          ],
        ),
      ),
    );
  }

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(text, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
      );
}
