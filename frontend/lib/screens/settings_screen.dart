import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../widgets/neon_button.dart';
import '../widgets/eq_visualizer.dart';
import '../widgets/gradient_background.dart';

/// Neon Pulse settings screen — điều chỉnh tốc độ, cao độ, âm lượng giọng đọc.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _serverUrlController = TextEditingController(text: 'http://192.168.1.100:8000');
  final _apiService = ApiService();

  @override
  void dispose() {
    _serverUrlController.dispose();
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
                audio.stop();
                Navigator.pop(context);
              },
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF141829),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF1E2A4A)),
                ),
                child: const Icon(
                  Icons.arrow_back_rounded,
                  size: 32,
                  color: Color(0xFF00F0FF),
                ),
              ),
            ),
          ),
          const Spacer(),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              const Text(
                'Cài đặt',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const Text(
                'Tùy chỉnh giọng đọc',
                style: TextStyle(
                  fontSize: 14,
                  color: Color(0xFF8892B0),
                ),
              ),
            ],
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
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Color(0xFF00F0FF),
          ),
        ),
        const SizedBox(height: 4),
        Container(height: 1, color: const Color(0xFF1E2A4A)),
      ],
    );
  }

  Widget _buildAdjustmentCard(BuildContext context, AudioService audio) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF141829),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF1E2A4A)),
      ),
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
                style: const TextStyle(
                  fontSize: 22,
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
                style: const TextStyle(
                  fontSize: 22,
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
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const Spacer(),
              Text(
                _getVolumeLabel(audio.volume),
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

  Widget _buildServerCard(BuildContext context, AudioService audio) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF141829),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF1E2A4A)),
      ),
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
          const SizedBox(height: 12),
          NeonButton(
            icon: Icons.save,
            label: 'Lưu địa chỉ',
            color: const Color(0xFF00F0FF),
            onTap: () {
              final url = _serverUrlController.text.trim();
              if (url.isNotEmpty) {
                _apiService.setBaseUrl(url);
                audio.speak('Đã lưu địa chỉ máy chủ');
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildAppInfoCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF141829),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF1E2A4A)),
      ),
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
