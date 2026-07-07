import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// A visual + semantic indicator for TTS/STT voice states with Neon Pulse
/// theme styling.
///
/// Displays a 56×56 circular indicator that animates color, border glow,
/// icon, and pulse opacity based on the current voice state. Designed for
/// blind users (Semantics + haptic feedback) and partially sighted users
/// (bright neon colours).
class VoiceIndicator extends StatefulWidget {
  /// Whether speech (TTS) is currently active.
  final bool isSpeaking;

  /// Whether the app is currently listening (STT).
  final bool isListening;

  /// Whether speech is paused.
  final bool isPaused;

  /// Optional callback to toggle or dismiss the active state.
  final VoidCallback? onTap;

  const VoiceIndicator({
    super.key,
    this.isSpeaking = false,
    this.isListening = false,
    this.isPaused = false,
    this.onTap,
  });

  @override
  State<VoiceIndicator> createState() => _VoiceIndicatorState();
}

class _VoiceIndicatorState extends State<VoiceIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;
  late final Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    );
    _pulseAnimation = Tween<double>(begin: 0.6, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _syncPulse();
  }

  @override
  void didUpdateWidget(VoiceIndicator old) {
    super.didUpdateWidget(old);
    // Haptic feedback on any state transition.
    if (widget.isListening != old.isListening ||
        widget.isSpeaking != old.isSpeaking ||
        widget.isPaused != old.isPaused) {
      HapticFeedback.selectionClick();
    }
    _syncPulse();
  }

  /// Starts or stops the pulse animation based on [widget.isListening].
  void _syncPulse() {
    if (widget.isListening) {
      if (!_pulseController.isAnimating) {
        _pulseController.repeat(reverse: true);
      }
    } else {
      _pulseController.stop();
      _pulseController.value = 1.0;
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  /// Resolve the current neon colour, icon, and semantic label.
  (Color color, IconData icon, String label) _resolveState() {
    if (widget.isListening) {
      return (
        const Color(0xFF39FF14), // lime green
        Icons.mic,
        'Listening for speech input.',
      );
    }
    if (widget.isSpeaking && widget.isPaused) {
      return (
        const Color(0xFFFFB300), // amber
        Icons.pause,
        'Speech paused. Tap to resume.',
      );
    }
    if (widget.isSpeaking) {
      return (
        const Color(0xFF00F0FF), // cyan
        Icons.volume_up,
        'Speaking.',
      );
    }
    return (
      const Color(0xFF8892B0), // grey
      Icons.mic_none,
      'Idle. No speech activity.',
    );
  }

  @override
  Widget build(BuildContext context) {
    final (color, icon, label) = _resolveState();
    final bool isActive = widget.isListening || widget.isSpeaking;

    final boxShadow = isActive
        ? [
            BoxShadow(
              color: color.withValues(alpha: 0.3),
              blurRadius: 10,
              spreadRadius: 3,
            ),
          ]
        : null;

    // Core indicator – AnimatedContainer handles smooth colour / shadow /
    // border transitions over 300 ms.
    Widget indicator = AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        color: color.withValues(alpha: isActive ? 0.2 : 0.1),
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 3),
        boxShadow: boxShadow,
      ),
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 300),
        child: Icon(
          icon,
          key: ValueKey(icon),
          size: 32,
          color: Colors.white,
        ),
      ),
    );

    // Pulse layer – only active when listening.
    if (widget.isListening) {
      indicator = AnimatedBuilder(
        animation: _pulseAnimation,
        builder: (_, child) => Opacity(
          opacity: _pulseAnimation.value,
          child: child,
        ),
        child: indicator,
      );
    }

    return Semantics(
      button: widget.onTap != null,
      label: label,
      child: GestureDetector(
        onTap: widget.onTap,
        child: indicator,
      ),
    );
  }
}
