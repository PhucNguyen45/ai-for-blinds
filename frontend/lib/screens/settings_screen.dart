import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../services/storage_service.dart';
import '../theme/app_theme.dart';

/// Settings screen — điều chỉnh tốc độ, cao độ, âm lượng giọng đọc.
/// Tuân thủ thiết kế SgBe Vision: slider đơn giản, nút test, không trang trí.
class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

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
                  displayValue: audio.speechRate.toStringAsFixed(1),
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
                  displayValue: audio.pitch.toStringAsFixed(1),
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
                  displayValue: audio.volume.toStringAsFixed(1),
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

                // Địa chỉ máy chủ
                _ServerAddressField(
                  cardColor: cardColor,
                  borderColor: borderColor,
                  theme: theme,
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

/// Ô nhập địa chỉ máy chủ. Không có ô này thì đổi máy chủ phải build lại app.
class _ServerAddressField extends StatefulWidget {
  const _ServerAddressField({
    required this.cardColor,
    required this.borderColor,
    required this.theme,
  });

  final Color cardColor;
  final Color borderColor;
  final ThemeData theme;

  @override
  State<_ServerAddressField> createState() => _ServerAddressFieldState();
}

class _ServerAddressFieldState extends State<_ServerAddressField> {
  final _controller = TextEditingController(text: ApiService.activeBaseUrl);
  final _storage = StorageService();
  bool _checking = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final audio = context.read<AudioService>();
    HapticFeedback.mediumImpact();
    setState(() => _checking = true);

    final url = _controller.text.trim();
    ApiService.configure(url);
    await _storage.saveBackendUrl(url);

    final reachable = await ApiService().isBackendAvailable();
    if (!mounted) return;
    setState(() => _checking = false);

    await audio.stop();
    await audio.speak(reachable
        ? 'Đã lưu địa chỉ máy chủ và kết nối được.'
        : 'Đã lưu địa chỉ nhưng chưa kết nối được máy chủ. '
            'Hãy kiểm tra lại địa chỉ và mạng.');
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: widget.cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: widget.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Địa chỉ máy chủ', style: widget.theme.textTheme.titleLarge),
          const SizedBox(height: 8),
          Semantics(
            label: 'Địa chỉ máy chủ backend',
            textField: true,
            child: TextField(
              controller: _controller,
              keyboardType: TextInputType.url,
              autocorrect: false,
              style: widget.theme.textTheme.bodyLarge,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'http://10.0.2.2:8000',
              ),
            ),
          ),
          const SizedBox(height: 12),
          Semantics(
            button: true,
            label: 'Lưu và kiểm tra kết nối máy chủ',
            child: SizedBox(
              width: double.infinity,
              height: 80,
              child: ElevatedButton(
                onPressed: _checking ? null : _save,
                child: Text(
                  _checking ? 'Đang kiểm tra...' : 'LƯU VÀ KIỂM TRA',
                  style: widget.theme.textTheme.titleLarge,
                ),
              ),
            ),
          ),
        ],
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
            Slider(
              value: value,
              min: min,
              max: max,
              divisions: divisions,
              label: '$label: $displayValue',
              onChanged: onChanged,
            ),
          ],
        ),
      ),
    );
  }
}
