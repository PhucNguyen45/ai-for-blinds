import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../models/learning_moment.dart';
import '../services/audio_service.dart';
import '../services/camera_service.dart';
import '../theme/app_theme.dart';
import '../widgets/big_button.dart';
import '../widgets/mode_selector.dart';

/// Scanner screen where students capture book pages, documents, or diagrams.
/// Features:
/// - ModeSelector: chọn OCR / Mô tả ảnh / Đọc biểu đồ
/// - BigButton "CHỤP ẢNH" ở giữa
/// - LinearProgressIndicator khi đang xử lý
/// - TTS tự động đọc kết quả sau khi xử lý
class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final CameraService _cameraService = CameraService();
  final ApiService _apiService = ApiService();
  final StorageService _storage = StorageService();

  ScanMode _selectedMode = ScanMode.ocr;
  bool _isProcessing = false;
  String? _resultText;

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
          break;

        case ScanMode.describe:
          // Use Gemini to describe the image
          result = await _apiService.describeImage(photo);
          break;

        case ScanMode.chart:
          // Use Gemini to describe the chart/data
          result = await _apiService.describeImage(photo);
          // Future: add specific chart sonification via /sonify endpoint
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

        // Keep it so the student can hear it again from Ôn tập later.
        await _saveMoment(photo, result);
      } else {
        setState(() {
          _isProcessing = false;
          _resultText = null;
        });

        final audio = context.read<AudioService>();
        await audio.stop();
        await audio.speak('Không tìm thấy nội dung. Hãy thử chụp lại với ánh sáng tốt hơn.');
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

  /// Store what was just read aloud, so the Ôn tập screen has something to
  /// show. Without this the review list is always empty.
  Future<void> _saveMoment(File photo, String result) async {
    const labels = {
      ScanMode.ocr: 'Đọc văn bản',
      ScanMode.describe: 'Mô tả ảnh',
      ScanMode.chart: 'Đọc biểu đồ',
    };
    final now = DateTime.now();
    await _storage.saveLearningMoment(
      LearningMoment(
        id: now.microsecondsSinceEpoch.toString(),
        title: '${labels[_selectedMode]} · '
            '${now.day}/${now.month} ${now.hour}:'
            '${now.minute.toString().padLeft(2, '0')}',
        description: result,
        imagePath: photo.path,
        textContent: result,
        createdAt: now,
      ),
    );
  }

  void _speakResult() {
    if (_resultText != null && _resultText!.isNotEmpty) {
      context.read<AudioService>().stop();
      context.read<AudioService>().speak(_resultText!);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final bgColor = isDark ? AppTheme.pureBlack : AppTheme.pureWhite;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Quét tài liệu'),
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
        child: SafeArea(
          child: Column(
            children: [
              // Mode selector
              ModeSelector(
                selectedMode: _selectedMode,
                onModeChanged: (mode) {
                  setState(() => _selectedMode = mode);
                  HapticFeedback.lightImpact();
                  final labels = {
                    ScanMode.ocr: 'Chế độ đọc văn bản',
                    ScanMode.describe: 'Chế độ mô tả ảnh',
                    ScanMode.chart: 'Chế độ đọc biểu đồ',
                  };
                  context.read<AudioService>().stop();
                  context.read<AudioService>().speak(labels[mode]!);
                },
              ),

              const SizedBox(height: 12),

              // Processing indicator
              if (_isProcessing)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 32),
                  child: Semantics(
                    label: 'Đang xử lý.',
                    child: Column(
                      children: [
                        const LinearProgressIndicator(minHeight: 6),
                        const SizedBox(height: 12),
                        Text(
                          'Đang xử lý...',
                          style: theme.textTheme.titleMedium,
                        ),
                      ],
                    ),
                  ),
                ),

              // Camera button area
              Expanded(
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (!_isProcessing) ...[
                        BigCircleButton(
                          icon: Icons.camera_alt_rounded,
                          label: 'CHỤP ẢNH',
                          color: AppTheme.primaryBlue,
                          onTap: _takePhoto,
                        ),
                        const SizedBox(height: 20),
                        Text(
                          'CHỤP ẢNH',
                          style: theme.textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Đưa camera vào tài liệu\nvà nhấn nút để chụp',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.grey.shade500,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),

              // Result / controls area
              if (_resultText != null && _resultText!.isNotEmpty)
                Container(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                  color: isDark ? AppTheme.darkCard : Colors.grey.shade50,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Semantics(
                        label: 'Kết quả. $_resultText',
                        child: Container(
                          width: double.infinity,
                          constraints: const BoxConstraints(maxHeight: 120),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: isDark ? AppTheme.pureBlack : AppTheme.pureWhite,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: isDark ? Colors.grey.shade700 : Colors.grey.shade300,
                            ),
                          ),
                          child: SingleChildScrollView(
                            child: Text(
                              _resultText!,
                              style: theme.textTheme.bodyMedium?.copyWith(height: 1.4),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          BigMediaButton(
                            icon: Icons.volume_up_rounded,
                            label: 'Nghe lại',
                            color: AppTheme.accentGreen,
                            onTap: _speakResult,
                          ),
                          BigMediaButton(
                            icon: Icons.camera_alt_rounded,
                            label: 'Chụp lại',
                            color: AppTheme.primaryBlue,
                            onTap: () {
                              setState(() => _resultText = null);
                              _takePhoto();
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
