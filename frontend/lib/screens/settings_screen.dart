import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../theme/app_theme.dart';
import '../widgets/big_button.dart';

/// Settings screen — điều chỉnh tốc độ, cao độ, âm lượng giọng đọc.
/// Tuân thủ thiết kế SgBe Vision: slider đơn giản, nút test, không trang trí.
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
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final bgColor = isDark ? AppTheme.pureBlack : AppTheme.pureWhite;
    final cardColor = isDark ? AppTheme.darkCard : AppTheme.pureWhite;
    final borderColor = isDark ? Colors.grey.shade700 : Colors.grey.shade300;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Cài đặt'),
        backgroundColor: isDark ? AppTheme.pureBlack : AppTheme.primaryBlue,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, size: 32),
          onPressed: () {
            context.read<AudioService>().stop();
            Navigator.pop(context);
          },
        ),
      ),
      body: Container(
        color: bgColor,
        child: Consumer<AudioService>(
          builder: (context, audio, _) {
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const SizedBox(height: 8),

                // Tốc độ giọng đọc
                _SettingSlider(
                  label: 'Tốc độ giọng đọc',
                  value: audio.speechRate,
                  min: 0.2,
                  max: 1.0,
                  divisions: 8,
                  displayValue: _getSpeedLabel(audio.speechRate),
                  sliderSemanticLabel: 'Tốc độ: ${_getSpeedLabel(audio.speechRate)}',
                  onChanged: (val) => audio.setSpeechRate(val),
                  cardColor: cardColor,
                  borderColor: borderColor,
                  theme: theme,
                ),
                const SizedBox(height: 12),

                // Cao độ giọng đọc
                _SettingSlider(
                  label: 'Cao độ giọng đọc',
                  value: audio.pitch,
                  min: 0.5,
                  max: 2.0,
                  divisions: 6,
                  displayValue: _getPitchLabel(audio.pitch),
                  sliderSemanticLabel: 'Cao độ: ${_getPitchLabel(audio.pitch)}',
                  onChanged: (val) => audio.setPitch(val),
                  cardColor: cardColor,
                  borderColor: borderColor,
                  theme: theme,
                ),
                const SizedBox(height: 12),

                // Âm lượng
                _SettingSlider(
                  label: 'Âm lượng',
                  value: audio.volume,
                  min: 0.0,
                  max: 1.0,
                  divisions: 5,
                  displayValue: _getVolumeLabel(audio.volume),
                  sliderSemanticLabel: 'Âm lượng: ${_getVolumeLabel(audio.volume)}',
                  onChanged: (val) => audio.setVolume(val),
                  cardColor: cardColor,
                  borderColor: borderColor,
                  theme: theme,
                ),

                const SizedBox(height: 24),

                // Nút kiểm tra
                Semantics(
                  button: true,
                  label: 'Kiểm tra cài đặt giọng đọc.',
                  child: GestureDetector(
                    onTap: () {
                      HapticFeedback.mediumImpact();
                      audio.speak(
                        'Đây là giọng đọc hiện tại của bạn. '
                        'Nếu bạn nghe rõ, cài đặt đã phù hợp.',
                      );
                    },
                    child: Container(
                      width: double.infinity,
                      constraints: const BoxConstraints(minHeight: 72),
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                      decoration: BoxDecoration(
                        color: AppTheme.accentGreen,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Center(
                        child: Text(
                          'Kiểm tra giọng đọc',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 32),

                // Cấu hình máy chủ
                const SizedBox(height: 16),
                Text(
                  'Cấu hình máy chủ',
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Semantics(
                  textField: true,
                  label: 'Địa chỉ máy chủ',
                  child: TextField(
                    decoration: const InputDecoration(
                      labelText: 'Địa chỉ máy chủ API',
                      hintText: 'http://192.168.1.100:8000',
                      border: OutlineInputBorder(),
                    ),
                    controller: _serverUrlController,
                    keyboardType: TextInputType.url,
                  ),
                ),
                const SizedBox(height: 8),
                BigButton(
                  icon: Icons.save,
                  label: 'Lưu địa chỉ máy chủ',
                  onTap: () {
                    final url = _serverUrlController.text.trim();
                    if (url.isNotEmpty) {
                      _apiService.setBaseUrl(url);
                      audio.speak('Đã lưu địa chỉ máy chủ');
                    }
                  },
                ),

                const SizedBox(height: 32),

                // Thông tin ứng dụng
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: cardColor,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: borderColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'SgBe Vision v1.0.0',
                        style: theme.textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Trợ lý học tập AI cho học sinh khiếm thị.',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: isDark ? Colors.grey.shade400 : Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 32),
              ],
            );
          },
        ),
      ),
    );
  }
}

/// Một slider đơn giản với nhãn và giá trị.
class _SettingSlider extends StatelessWidget {
  final String label;
  final double value;
  final double min;
  final double max;
  final int divisions;
  final String displayValue;
  final String sliderSemanticLabel;
  final ValueChanged<double> onChanged;
  final Color cardColor;
  final Color borderColor;
  final ThemeData theme;

  const _SettingSlider({
    required this.label,
    required this.value,
    required this.min,
    required this.max,
    required this.divisions,
    required this.displayValue,
    required this.sliderSemanticLabel,
    required this.onChanged,
    required this.cardColor,
    required this.borderColor,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '$label. $displayValue',
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: cardColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: borderColor),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  label,
                  style: theme.textTheme.titleLarge,
                ),
                const Spacer(),
                Text(
                  displayValue,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            Semantics(
              slider: true,
              value: value.toStringAsFixed(1),
              label: sliderSemanticLabel,
              child: Slider(
                value: value,
                min: min,
                max: max,
                divisions: divisions,
                label: sliderSemanticLabel,
                onChanged: onChanged,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
