import 'package:flutter/material.dart';

/// A small visual + semantic indicator that shows when TTS or STT is active.
/// Designed for blind users: provides audio feedback via Semantics
/// and a visible indicator for partially sighted users.
class VoiceIndicator extends StatelessWidget {
  /// Whether speech (TTS) is currently active.
  final bool isSpeaking;

  /// Whether the app is currently listening (STT).
  final bool isListening;

  /// Whether speech is paused.
  final bool isPaused;

  /// Optional callback to toggle the active state.
  final VoidCallback? onTap;

  const VoiceIndicator({
    super.key,
    this.isSpeaking = false,
    this.isListening = false,
    this.isPaused = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final bool isActive = isSpeaking || isListening;
    final String label;
    final IconData icon;
    final Color color;

    if (isListening) {
      label = 'Listening for speech input.';
      icon = Icons.mic_rounded;
      color = const Color(0xFF2E7D32); // green
    } else if (isSpeaking && isPaused) {
      label = 'Speech paused. Tap to resume.';
      icon = Icons.pause_circle_rounded;
      color = const Color(0xFFFF8F00); // orange
    } else if (isSpeaking) {
      label = 'Speaking.';
      icon = Icons.volume_up_rounded;
      color = const Color(0xFF1565C0); // blue
    } else {
      label = 'Idle. No speech activity.';
      icon = Icons.mic_none_rounded;
      color = Colors.grey;
    }

    return Semantics(
      button: onTap != null,
      label: label,
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: isActive ? color.withValues(alpha: 0.15) : Colors.transparent,
            shape: BoxShape.circle,
            border: isActive
                ? Border.all(color: color, width: 2)
                : null,
          ),
          child: Icon(
            icon,
            size: 28,
            color: color,
          ),
        ),
      ),
    );
  }
}
