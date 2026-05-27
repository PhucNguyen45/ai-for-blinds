import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/tts_service.dart';
import '../theme/app_theme.dart';
import '../widgets/big_button.dart';

/// Screen where users type or paste text to have it read aloud.
/// Simplified for blind users: big text area, big buttons, no decorations.
class TextReaderScreen extends StatefulWidget {
  const TextReaderScreen({super.key});

  @override
  State<TextReaderScreen> createState() => _TextReaderScreenState();
}

class _TextReaderScreenState extends State<TextReaderScreen> {
  final TextEditingController _textController = TextEditingController();
  final FocusNode _textFocusNode = FocusNode();

  @override
  void dispose() {
    _textController.dispose();
    _textFocusNode.dispose();
    super.dispose();
  }

  void _speak(TtsService tts) {
    final text = _textController.text.trim();
    if (text.isEmpty) {
      _showSnackBar('Enter some text first.');
      return;
    }
    HapticFeedback.mediumImpact();
    tts.speak(text);
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), duration: const Duration(seconds: 2)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Consumer<TtsService>(
      builder: (context, tts, _) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('Text Reader'),
            backgroundColor: isDark ? AppTheme.pureBlack : AppTheme.primaryBlue,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_rounded, size: 32),
              onPressed: () {
                tts.stop();
                Navigator.pop(context);
              },
            ),
          ),
          body: SafeArea(
            child: Column(
              children: [
                // Text input
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Semantics(
                      label: 'Text input. Type or paste text to be read aloud.',
                      child: TextField(
                        controller: _textController,
                        focusNode: _textFocusNode,
                        maxLines: null,
                        expands: true,
                        textAlignVertical: TextAlignVertical.top,
                        style: theme.textTheme.bodyLarge?.copyWith(height: 1.6),
                        decoration: InputDecoration(
                          hintText: 'Type or paste text here...',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          filled: true,
                          fillColor: isDark ? AppTheme.darkCard : Colors.grey.shade50,
                        ),
                      ),
                    ),
                  ),
                ),

                // Controls
                Container(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                  color: isDark ? AppTheme.pureBlack : AppTheme.pureWhite,
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
                                : (tts.isSpeaking ? 'Pause' : 'Speak'),
                            color: AppTheme.accentGreen,
                            onTap: () {
                              if (tts.isSpeaking) {
                                if (tts.isPaused) {
                                  tts.resume();
                                } else {
                                  tts.pause();
                                }
                              } else {
                                _speak(tts);
                              }
                            },
                          ),
                          BigMediaButton(
                            icon: Icons.stop_rounded,
                            label: 'Stop',
                            color: AppTheme.accentRed,
                            onTap: () {
                              HapticFeedback.lightImpact();
                              tts.stop();
                            },
                          ),
                          BigMediaButton(
                            icon: Icons.clear_all_rounded,
                            label: 'Clear',
                            color: Colors.grey.shade600,
                            onTap: () {
                              HapticFeedback.lightImpact();
                              tts.stop();
                              _textController.clear();
                            },
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      // Speed slider - plain, no decorative icons
                      Semantics(
                        label: 'Speech speed. ${tts.speechRate.toStringAsFixed(1)}',
                        child: Row(
                          children: [
                            const Text('Slow', style: TextStyle(fontSize: 16)),
                            Expanded(
                              child: Slider(
                                value: tts.speechRate,
                                min: 0.2,
                                max: 1.0,
                                divisions: 8,
                                label: 'Speed ${tts.speechRate.toStringAsFixed(1)}',
                                onChanged: (val) => tts.setSpeechRate(val),
                              ),
                            ),
                            const Text('Fast', style: TextStyle(fontSize: 16)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
