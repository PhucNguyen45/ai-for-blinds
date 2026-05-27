import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../services/ocr_service.dart';
import '../services/tts_service.dart';
import '../theme/app_theme.dart';
import '../widgets/big_button.dart';

/// Screen where blind students point their camera at a book page.
/// Pure function: take photo → extract text → read aloud.
class BookScannerScreen extends StatefulWidget {
  const BookScannerScreen({super.key});

  @override
  State<BookScannerScreen> createState() => _BookScannerScreenState();
}

class _BookScannerScreenState extends State<BookScannerScreen> {
  final OcrService _ocrService = OcrService();
  final ApiService _apiService = ApiService();
  final ImagePicker _picker = ImagePicker();

  bool _isProcessing = false;
  String? _extractedText;

  @override
  void dispose() {
    _ocrService.dispose();
    super.dispose();
  }

  Future<void> _scanBookPage() async {
    HapticFeedback.mediumImpact();

    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1920,
        maxHeight: 2560,
        imageQuality: 85,
        preferredCameraDevice: CameraDevice.rear,
      );

      if (photo == null) return;

      setState(() {
        _isProcessing = true;
        _extractedText = null;
      });

      // Try backend → local OCR
      String? result = await _apiService.describeImage(File(photo.path));
      if (result == null || result.isEmpty) {
        result = await _apiService.ocrImage(File(photo.path));
      }
      if (result == null || result.isEmpty) {
        result = await _ocrService.extractTextFromImage(File(photo.path));
      }

      if (!mounted) return;

      if (result != null && result.isNotEmpty) {
        setState(() {
          _extractedText = result;
          _isProcessing = false;
        });

        final tts = context.read<TtsService>();
        await tts.stop();
        await tts.speak(result);

        HapticFeedback.heavyImpact();
      } else {
        setState(() => _isProcessing = false);
        _showSnackBar('No text found. Try again.');
      }
    } catch (e) {
      debugPrint('Scan error: $e');
      if (mounted) {
        setState(() => _isProcessing = false);
        _showSnackBar('Failed to scan. Try again.');
      }
    }
  }

  void _retakePhoto() {
    context.read<TtsService>().stop();
    setState(() => _extractedText = null);
    _scanBookPage();
  }

  void _showSnackBar(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), duration: const Duration(seconds: 3)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final bgColor = isDark ? AppTheme.pureBlack : AppTheme.pureWhite;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Book Scanner'),
        backgroundColor: isDark ? AppTheme.pureBlack : AppTheme.primaryBlue,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, size: 32),
          onPressed: () {
            context.read<TtsService>().stop();
            Navigator.pop(context);
          },
        ),
      ),
      body: Container(
        color: bgColor,
        child: SafeArea(
          child: _isProcessing
              ? _buildProcessingView(theme)
              : _extractedText != null
                  ? _buildResultView(theme, isDark)
                  : _buildScanPrompt(),
        ),
      ),
    );
  }

  Widget _buildScanPrompt() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(height: 24),
          BigCircleButton(
            icon: Icons.camera_alt_rounded,
            label: 'Scan book page',
            color: AppTheme.primaryBlue,
            onTap: _scanBookPage,
          ),
          const SizedBox(height: 24),
          const Text(
            'Tap to scan',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Widget _buildProcessingView(ThemeData theme) {
    return Center(
      child: Semantics(
        label: 'Processing. Please wait.',
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(
              width: 64,
              height: 64,
              child: CircularProgressIndicator(strokeWidth: 6),
            ),
            const SizedBox(height: 24),
            Text(
              'Reading...',
              style: theme.textTheme.headlineMedium,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultView(ThemeData theme, bool isDark) {
    return Consumer<TtsService>(
      builder: (context, tts, _) {
        return Column(
          children: [
            // Text content
            Expanded(
              child: Semantics(
                label: 'Extracted text. $_extractedText',
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: SelectableText(
                    _extractedText!,
                    style: theme.textTheme.bodyLarge?.copyWith(
                      height: 1.7,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
            ),

            // Controls
            Container(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              color: isDark ? AppTheme.darkCard : AppTheme.pureWhite,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      BigMediaButton(
                        icon: tts.isSpeaking && !tts.isPaused
                            ? Icons.pause_rounded
                            : Icons.play_arrow_rounded,
                        label: tts.isPaused
                            ? 'Resume'
                            : (tts.isSpeaking ? 'Pause' : 'Read'),
                        color: AppTheme.accentGreen,
                        onTap: () {
                          if (tts.isSpeaking && !tts.isPaused) {
                            tts.pause();
                          } else if (tts.isPaused) {
                            tts.resume();
                          } else {
                            tts.speak(_extractedText!);
                          }
                        },
                      ),
                      BigMediaButton(
                        icon: Icons.stop_rounded,
                        label: 'Stop',
                        color: AppTheme.accentRed,
                        onTap: () => tts.stop(),
                      ),
                      BigMediaButton(
                        icon: Icons.camera_alt_rounded,
                        label: 'Scan again',
                        color: AppTheme.primaryBlue,
                        onTap: _retakePhoto,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
