import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models/scan_mode.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../services/camera_service.dart';
import '../services/local_ocr_service.dart';
import '../services/settings_service.dart';
import '../utils/responsive.dart';
import '../widgets/neon_button.dart';
import '../widgets/glow_chip.dart';
import '../widgets/waveform_bar.dart';
import '../widgets/glass_bottom_sheet.dart';

/// Scanner screen where students capture book pages, documents, or diagrams.
///
/// Neon Pulse design featuring:
/// - GlowChipBar mode selection (OCR / Describe / Chart / Detect)
/// - NeonCircleButton camera trigger
/// - WaveformBar processing animation
/// - GlassBottomSheetContainer for results
/// - TTS tự động đọc kết quả sau khi xử lý
class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final CameraService _cameraService = CameraService();
  final ApiService _apiService = ApiService();
  final LocalOcrService _localOcr = LocalOcrService();

  ScanMode _selectedMode = ScanMode.ocr;
  bool _isProcessing = false;
  String? _resultText;

  static const List<Color> _modeColors = [
    Color(0xFF00F0FF), // OCR – cyan
    Color(0xFF9D4EDD), // Describe – purple
    Color(0xFFFFB300), // Chart – amber
    Color(0xFF39FF14), // Detect – lime
    Color(0xFFFFD700), // Money – gold
  ];

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _takePhoto() async {
    HapticFeedback.mediumImpact();

    try {
      final File? photo = await _cameraService.takePhoto();
      if (photo == null) return;

      if (!mounted) return;
      setState(() {
        _isProcessing = true;
        _resultText = null;
      });

      String? result;

      switch (_selectedMode) {
        case ScanMode.ocr:
          // Try backend OCR → API service
          result = await _apiService.ocrImage(photo);
          if (result == null || result.isEmpty) {
            // Fallback to on-device OCR
            await _localOcr.init();
            result = await _localOcr.extractText(photo);
          }
          break;

        case ScanMode.describe:
          // Use Gemini to describe the image
          result = await _apiService.describeImage(photo);
          break;

        case ScanMode.chart:
          // Try sonification API first
          final sonifyResult = await _apiService.sonifyData(
            dataPoints: [
              {'label': 'Dữ liệu 1', 'value': 10},
              {'label': 'Dữ liệu 2', 'value': 20},
              {'label': 'Dữ liệu 3', 'value': 15},
            ],
            chartType: 'bar',
          );
          if (sonifyResult != null) {
            result = sonifyResult['summary'] as String? ??
                sonifyResult['description'] as String?;
          } else {
            // Fallback to Gemini description
            result = await _apiService.describeImage(photo);
          }
          break;

        case ScanMode.detect:
          final detectMap = await _apiService.detectImage(photo);
          if (detectMap != null) {
            final objects = detectMap['objects'] as List?;
            final sceneDesc = detectMap['scene_description'] as String?;
            if (objects != null && objects.isNotEmpty) {
              result =
                  sceneDesc ?? 'Phát hiện ${objects.length} vật thể';
            } else {
              result = detectMap['scene_description'] as String? ??
                  'Không phát hiện vật thể nào.';
            }
          }
          break;

        case ScanMode.money:
          final moneyMap = await _apiService.recognizeMoney(photo);
          if (moneyMap != null) {
            final formatted = moneyMap['formatted'] as String?;
            final confidence = moneyMap['confidence'];
            if (formatted != null && formatted.isNotEmpty) {
              result = 'Tờ tiền $formatted';
              if (confidence is num && confidence > 0) {
                result =
                    '$result. Độ tin cậy ${(confidence * 100).round()} phần trăm.';
              }
            } else {
              result = 'Không phát hiện tờ tiền Việt Nam trong ảnh.';
            }
          }
          break;
      }

      if (!mounted) return;

      if (result != null && result.isNotEmpty) {
        setState(() {
          _resultText = result;
          _isProcessing = false;
        });

        // Auto-read the result
        final audio = context.read<AudioService>();
        await audio.stop();
        await audio.speak(result);
        HapticFeedback.heavyImpact();
      } else {
        setState(() {
          _isProcessing = false;
          _resultText = null;
        });

        final audio = context.read<AudioService>();
        await audio.stop();
        await audio.speak(
            'Không tìm thấy nội dung. Hãy thử chụp lại với ánh sáng tốt hơn.');
      }
    } catch (e) {
      debugPrint('Scanner error: $e');
      if (mounted) {
        setState(() => _isProcessing = false);
        final audio = context.read<AudioService>();
        await audio.stop();
        await audio.speak('Có lỗi xảy ra. Xin thử lại.');
      }
    }
  }

  void _speakResult() {
    if (_resultText != null && _resultText!.isNotEmpty) {
      context.read<AudioService>().stop();
      context.read<AudioService>().speak(_resultText!);
    }
  }

  /// Save the current scan result as a persistent learning moment.
  Future<void> _saveMoment() async {
    final result = _resultText;
    if (result == null || result.isEmpty) return;

    final settings = await SettingsService().load();
    if (!mounted) return;
    if (settings.deviceId.isEmpty) {
      context.read<AudioService>().speak('Chưa có định danh thiết bị.');
      return;
    }

    final contentType = switch (_selectedMode) {
      ScanMode.ocr => 'ocr',
      ScanMode.describe => 'image_description',
      ScanMode.detect => 'image_description',
      ScanMode.money => 'image_description',
      ScanMode.chart => 'description',
    };

    final title = _resultTitle(settings, contentType);
    final moment = await _apiService.createMoment(
      deviceId: settings.deviceId,
      title: title,
      content: result,
      contentType: contentType,
    );

    if (!mounted) return;
    final audio = context.read<AudioService>();
    await audio.stop();
    if (moment != null) {
      audio.speak('Đã lưu khoảnh khắc học tập.');
    } else {
      audio.speak('Không thể lưu khoảnh khắc. Hãy kiểm tra kết nối máy chủ.');
    }
  }

  String _resultTitle(AppSettings settings, String contentType) {
    final base = switch (contentType) {
      'ocr' => 'Văn bản quét được',
      'image_description' => 'Mô tả hình ảnh',
      _ => 'Nội dung đã quét',
    };
    final firstLine = _resultText!.trim().split('\n').first;
    final preview = firstLine.length > 40
        ? '${firstLine.substring(0, 40)}…'
        : firstLine;
    return '$base: $preview';
  }

  @override
  Widget build(BuildContext context) {
    final modeItems = ScanMode.values.asMap().entries.map((entry) {
      final idx = entry.key;
      final mode = entry.value;
      return GlowChipData(
        label: mode.label,
        icon: mode.icon,
        color: _modeColors[idx],
      );
    }).toList();

    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      body: Stack(
        children: [
          // Dark background
          Container(color: const Color(0xFF0A0E1A)),

          // Main content area
          SafeArea(
            child: Column(
              children: [
                // ── Top section ───────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Semantics(
                        button: true,
                        label: 'Quay lại',
                        child: IconButton(
                          icon: const Icon(Icons.arrow_back, color: Colors.white),
                          onPressed: () {
                            HapticFeedback.mediumImpact();
                            context.read<AudioService>().stop();
                            Navigator.pop(context);
                          },
                        ),
                      ),
                      const Spacer(),
                      Text(
                        'Quét tài liệu',
                        style: TextStyle(
                          fontSize: Responsive.textScale(context, 24, min: 18, max: 28),
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      // Balance the row so title is roughly centered
                      const SizedBox(width: 48),
                    ],
                  ),
                ),

                // ── Mode selector (GlowChipBar) ───────────────────────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: GlowChipBar(
                    items: modeItems,
                    selectedIndex: ScanMode.values.indexOf(_selectedMode),
                    onIndexChanged: (index) {
                      final mode = ScanMode.values[index];
                      setState(() => _selectedMode = mode);
                      HapticFeedback.lightImpact();
                      const labels = {
                        ScanMode.ocr: 'Chế độ đọc văn bản',
                        ScanMode.describe: 'Chế độ mô tả ảnh',
                        ScanMode.chart: 'Chế độ đọc biểu đồ',
                        ScanMode.detect: 'Chế độ phát hiện vật thể',
                        ScanMode.money: 'Chế độ nhận dạng tiền',
                      };
                      context.read<AudioService>().stop();
                      context.read<AudioService>().speak(labels[mode]!);
                    },
                  ),
                ),

                const SizedBox(height: 24),

                // ── Center camera / processing area ───────────────────
                Expanded(
                  child: Column(
                    children: [
                      if (!_isProcessing) ...[
                        NeonCircleButton(
                          icon: Icons.camera_alt,
                          label: 'CHỤP ẢNH',
                          size: Responsive.safeButtonSize(context, 160, min: 120, max: 180),
                          color: const Color(0xFF00F0FF),
                          onTap: _takePhoto,
                        ),
                        const SizedBox(height: 20),
                        Text(
                          'Chụp ảnh tài liệu',
                          style: TextStyle(
                            fontSize: Responsive.textScale(context, 20, min: 16, max: 24),
                            color: Color(0xFF8892B0),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Đưa camera vào tài liệu để quét',
                          style: TextStyle(
                            fontSize: Responsive.textScale(context, 16, min: 13, max: 20),
                            color: Color(0xFF4A5580),
                          ),
                        ),
                      ] else ...[
                        WaveformBar(
                          state: WaveformState.processing,
                          height: 60,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Đang xử lý...',
                          style: TextStyle(
                            fontSize: Responsive.textScale(context, 22, min: 16, max: 26),
                            fontWeight: FontWeight.bold,
                            color: Color(0xFFFFB300),
                          ),
                        ),
                      ],
                      const Spacer(flex: 1),
                    ],
                  ),
                ),

                // ── Result area (glass bottom sheet style) ────────────
                if (_resultText != null && _resultText!.isNotEmpty)
                  SizedBox(
                    height: (MediaQuery.of(context).size.height * 0.35).clamp(200, 350),
                    child: GlassBottomSheetContainer(
                      title: 'Kết quả',
                      icon: Icons.check_circle,
                      color: const Color(0xFF39FF14),
                      child: Column(
                        children: [
                          Expanded(
                            child: SingleChildScrollView(
                              child: Text(
                                _resultText!,
                                style: const TextStyle(
                                  fontSize: 16,
                                  color: Color(0xFFFFFFFF),
                                  height: 1.4,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Expanded(
                                child: NeonIconButton(
                                  icon: Icons.volume_up,
                                  label: 'Nghe lại',
                                  color: const Color(0xFF00F0FF),
                                  onTap: _speakResult,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: NeonIconButton(
                                  icon: Icons.save_alt,
                                  label: 'Lưu',
                                  color: const Color(0xFFFFD700),
                                  onTap: _saveMoment,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: NeonIconButton(
                                  icon: Icons.camera_alt,
                                  label: 'Chụp lại',
                                  color: const Color(0xFF9D4EDD),
                                  onTap: () {
                                    setState(() => _resultText = null);
                                    _takePhoto();
                                  },
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),

                // ── Bottom safe-area padding ───────────────────────────
                SizedBox(height: MediaQuery.of(context).padding.bottom),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
