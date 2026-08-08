import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../services/settings_service.dart';
import '../services/voice_controller.dart';
import '../utils/responsive.dart';
import '../widgets/neon_button.dart';
import '../widgets/eq_visualizer.dart';
import '../widgets/gradient_background.dart';

/// Neon Pulse settings screen — điều chỉnh tốc độ, cao độ, âm lượng giọng đọc,
/// cấu hình máy chủ và lựa chọn "luôn lắng nghe".
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _serverUrlController = TextEditingController(text: ApiService().baseUrl);
  final _apiKeyController = TextEditingController(text: ApiService().apiKey);
  bool _obscureKey = true;
  bool _testingConnection = false;
  bool _autoListen = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _autoListen = context.read<VoiceController>().autoListen;
    });
  }

  @override
  void dispose() {
    _serverUrlController.dispose();
    _apiKeyController.dispose();
    super.dispose();
  }

  String _getSpeedLabel(double speed) {
    if (speed < 0.4) return 'Chậm (${speed.toStringAsFixed(1)})';
    if (speed <= 0.7) return 'Bình thường (${speed.toStringAsFixed(1)})';
    return 'Nhanh (${speed.toStringAsFixed(1)})';
  }

  String _getPitchLabel(double pitch) {
    if (pitch < 0.8) return 'Trầm (${pitch.toStringAsFixed(1)})';
    if (pitch <= 1.5) return 'Bình thường (${pitch.toStringAsFixed(1)})';
    return 'Cao (${pitch.toStringAsFixed(1)})';
  }

  String _getVolumeLabel(double volume) {
    if (volume < 0.3) return 'Nhỏ (${volume.toStringAsFixed(1)})';
    if (volume <= 0.7) return 'Vừa (${volume.toStringAsFixed(1)})';
    return 'Lớn (${volume.toStringAsFixed(1)})';
  }

  Future<void> _saveSettings() async {
    final url = _serverUrlController.text.trim();
    final key = _apiKeyController.text.trim();
    final audio = context.read<AudioService>();
    final settings = AppSettings(
      serverUrl: url,
      apiKey: key,
      autoListen: _autoListen,
    );
    await SettingsService().save(settings);
    ApiService.configure(baseUrl: url, apiKey: key);
    audio.stop();
    audio.speak('Đã lưu cài đặt.');
  }

  Future<void> _testConnection() async {
    final audio = context.read<AudioService>();
    setState(() => _testingConnection = true);
    final ok = await ApiService().isBackendAvailable();
    if (!mounted) return;
    setState(() => _testingConnection = false);
    audio.stop();
    if (ok) {
      audio.speak('Kết nối máy chủ thành công.');
    } else {
      audio.speak(
        'Không kết nối được máy chủ. Hãy kiểm tra địa chỉ và mạng.',
      );
    }
  }

  void _onAutoListenChanged(bool value) {
    setState(() => _autoListen = value);
    final controller = context.read<VoiceController>();
    controller.autoListen = value;
    // Persist immediately so the choice survives restart.
    SettingsService().save(
      AppSettings(
        serverUrl: _serverUrlController.text.trim(),
        apiKey: _apiKeyController.text.trim(),
        autoListen: value,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        const GradientBackground(),
        SafeArea(
          child: Consumer<AudioService>(
            builder: (context, audio, _) {
              return Column(
                children: [
                  _buildTopBar(context, audio),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildSectionTitle('Giọng đọc'),
                          const SizedBox(height: 12),
                          EQVisualizer(
                            speed: audio.speechRate,
                            pitch: audio.pitch,
                            volume: audio.volume,
                          ),
                          const SizedBox(height: 24),
                          _buildSectionTitle('Điều chỉnh'),
                          const SizedBox(height: 12),
                          _buildAdjustmentCard(context, audio),
                          const SizedBox(height: 24),
                          _buildSectionTitle('Điều khiển bằng giọng nói'),
                          const SizedBox(height: 12),
                          _buildVoiceCard(context, audio),
                          const SizedBox(height: 24),
                          _buildSectionTitle('Máy chủ'),
                          const SizedBox(height: 12),
                          _buildServerCard(context, audio),
                          const SizedBox(height: 24),
                          _buildSectionTitle('Ứng dụng'),
                          const SizedBox(height: 12),
                          _buildAppInfoCard(),
                          const SizedBox(height: 32),
                        ],
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildTopBar(BuildContext context, AudioService audio) {
    return Padding(
      padding: const EdgeInsets.only(top: 16, left: 16, right: 16),
      child: Row(
        children: [
          Semantics(
            button: true,
            label: 'Quay lại',
            child: GestureDetector(
              onTap: () {
                HapticFeedback.mediumImpact();
                audio.stop();
                Navigator.pop(context);
              },
              behavior: HitTestBehavior.opaque,
              child: Padding(
                padding: const EdgeInsets.all(8),
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFF141829),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF1E2A4A)),
                  ),
                  child: const Padding(
                    padding: EdgeInsets.all(6),
                    child: Icon(
                      Icons.arrow_back_rounded,
                      size: 28,
                      color: Color(0xFF00F0FF),
                    ),
                  ),
                ),
              ),
            ),
          ),
          const Spacer(),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  'Cài đặt',
                  style: TextStyle(
                    fontSize: Responsive.textScale(context, 24, min: 18, max: 28),
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                Text(
                  'Tùy chỉnh giọng đọc',
                  style: TextStyle(
                    fontSize: Responsive.textScale(context, 14, min: 12, max: 18),
                    color: Color(0xFF8892B0),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            fontSize: Responsive.textScale(context, 20, min: 15, max: 24),
            fontWeight: FontWeight.bold,
            color: Color(0xFF00F0FF),
          ),
        ),
        const SizedBox(height: 4),
        Container(height: 1, color: const Color(0xFF1E2A4A)),
      ],
    );
  }

  Widget _buildCard({required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF141829),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF1E2A4A)),
      ),
      child: child,
    );
  }

  Widget _buildAdjustmentCard(BuildContext context, AudioService audio) {
    return _buildCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Tốc độ
          Row(
            children: [
              const Icon(Icons.speed, color: Color(0xFF00F0FF), size: 28),
              const SizedBox(width: 8),
              Text(
                'Tốc độ',
                style: TextStyle(
                  fontSize: Responsive.textScale(context, 22, min: 16, max: 26),
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const Spacer(),
              Text(
                _getSpeedLabel(audio.speechRate),
                style: const TextStyle(
                  fontSize: 16,
                  color: Color(0xFF8892B0),
                ),
              ),
            ],
          ),
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              activeTrackColor: const Color(0xFF00F0FF),
              inactiveTrackColor: const Color(0xFF1E2A4A),
              thumbColor: const Color(0xFF00F0FF),
              overlayColor: const Color(0xFF00F0FF).withValues(alpha: 0.15),
              valueIndicatorColor: const Color(0xFF00F0FF),
              valueIndicatorTextStyle: const TextStyle(
                color: Colors.black,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
            child: Slider(
              value: audio.speechRate,
              min: 0.2,
              max: 1.0,
              divisions: 8,
              label: _getSpeedLabel(audio.speechRate),
              onChanged: (val) => audio.setSpeechRate(val),
            ),
          ),

          const SizedBox(height: 16),

          // Cao độ
          Row(
            children: [
              const Icon(Icons.tune, color: Color(0xFF00F0FF), size: 28),
              const SizedBox(width: 8),
              Text(
                'Cao độ',
                style: TextStyle(
                  fontSize: Responsive.textScale(context, 22, min: 16, max: 26),
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const Spacer(),
              Text(
                _getPitchLabel(audio.pitch),
                style: const TextStyle(
                  fontSize: 16,
                  color: Color(0xFF8892B0),
                ),
              ),
            ],
          ),
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              activeTrackColor: const Color(0xFF00F0FF),
              inactiveTrackColor: const Color(0xFF1E2A4A),
              thumbColor: const Color(0xFF00F0FF),
              overlayColor: const Color(0xFF00F0FF).withValues(alpha: 0.15),
              valueIndicatorColor: const Color(0xFF00F0FF),
              valueIndicatorTextStyle: const TextStyle(
                color: Colors.black,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
            child: Slider(
              value: audio.pitch,
              min: 0.5,
              max: 2.0,
              divisions: 6,
              label: _getPitchLabel(audio.pitch),
              onChanged: (val) => audio.setPitch(val),
            ),
          ),

          const SizedBox(height: 16),

          // Âm lượng
          Row(
            children: [
              const Icon(Icons.volume_up, color: Color(0xFF00F0FF), size: 28),
              const SizedBox(width: 8),
              Text(
                'Âm lượng',
                style: TextStyle(
                  fontSize: Responsive.textScale(context, 22, min: 16, max: 26),
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const Spacer(),
              Text(
                _getVolumeLabel(audio.volume),
                style: TextStyle(
                  fontSize: Responsive.textScale(context, 16, min: 13, max: 20),
                  color: Color(0xFF8892B0),
                ),
              ),
            ],
          ),
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              activeTrackColor: const Color(0xFF00F0FF),
              inactiveTrackColor: const Color(0xFF1E2A4A),
              thumbColor: const Color(0xFF00F0FF),
              overlayColor: const Color(0xFF00F0FF).withValues(alpha: 0.15),
              valueIndicatorColor: const Color(0xFF00F0FF),
              valueIndicatorTextStyle: const TextStyle(
                color: Colors.black,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
            child: Slider(
              value: audio.volume,
              min: 0.0,
              max: 1.0,
              divisions: 5,
              label: _getVolumeLabel(audio.volume),
              onChanged: (val) => audio.setVolume(val),
            ),
          ),

          const SizedBox(height: 20),

          NeonButton(
            icon: Icons.volume_up,
            label: 'Kiểm tra giọng đọc',
            color: const Color(0xFF39FF14),
            glow: true,
            onTap: () {
              HapticFeedback.mediumImpact();
              audio.speak(
                'Đây là giọng đọc hiện tại của bạn. '
                'Nếu bạn nghe rõ, cài đặt đã phù hợp.',
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildVoiceCard(BuildContext context, AudioService audio) {
    return _buildCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.mic, color: Color(0xFF39FF14), size: 28),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Luôn lắng nghe',
                  style: TextStyle(
                    fontSize: Responsive.textScale(context, 22, min: 16, max: 26),
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
              Semantics(
                toggled: _autoListen,
                button: true,
                label: 'Luôn lắng nghe lệnh giọng nói',
                child: Switch(
                  value: _autoListen,
                  activeTrackColor: const Color(0xFF39FF14),
                  onChanged: _onAutoListenChanged,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Bật để ứng dụng tự lắng nghe lệnh sau khi đọc lời nhắc. '
            'Khi tắt, nhấn giữ màn hình hoặc lắc nhẹ máy để gọi giọng nói.',
            style: TextStyle(
              fontSize: 15,
              height: 1.4,
              color: Color(0xFF8892B0),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildServerCard(BuildContext context, AudioService audio) {
    return _buildCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            decoration: InputDecoration(
              labelText: 'Địa chỉ máy chủ API',
              labelStyle: const TextStyle(color: Color(0xFF8892B0)),
              hintText: 'http://192.168.1.100:8000',
              hintStyle: TextStyle(color: const Color(0xFF8892B0).withValues(alpha: 0.5)),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Color(0xFF1E2A4A)),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Color(0xFF00F0FF)),
              ),
              filled: true,
              fillColor: const Color(0xFF0A0E1A),
            ),
            style: const TextStyle(color: Colors.white),
            controller: _serverUrlController,
            keyboardType: TextInputType.url,
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextField(
                  decoration: InputDecoration(
                    labelText: 'Khóa API',
                    labelStyle: const TextStyle(color: Color(0xFF8892B0)),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(color: Color(0xFF1E2A4A)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(color: Color(0xFF00F0FF)),
                    ),
                    filled: true,
                    fillColor: const Color(0xFF0A0E1A),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscureKey
                            ? Icons.visibility_off
                            : Icons.visibility,
                        color: const Color(0xFF8892B0),
                      ),
                      onPressed: () =>
                          setState(() => _obscureKey = !_obscureKey),
                    ),
                  ),
                  style: const TextStyle(color: Colors.white),
                  controller: _apiKeyController,
                  obscureText: _obscureKey,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: NeonButton(
                  icon: Icons.cloud_upload,
                  label: 'Lưu cài đặt',
                  color: const Color(0xFF00F0FF),
                  onTap: _saveSettings,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: NeonButton(
                  icon: Icons.wifi_tethering,
                  label: _testingConnection ? 'Đang kiểm tra...' : 'Kiểm tra',
                  color: const Color(0xFF9D4EDD),
                  glow: !_testingConnection,
                  onTap: _testingConnection ? () {} : _testConnection,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAppInfoCard() {
    return _buildCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'SgBe Vision v1.0.0',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'Trợ lý học tập AI',
            style: TextStyle(
              fontSize: 16,
              color: Color(0xFF8892B0),
            ),
          ),
        ],
      ),
    );
  }
}
