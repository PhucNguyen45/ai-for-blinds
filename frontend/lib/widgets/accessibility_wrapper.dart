import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// A reusable wrapper that adds Semantics labels and haptic feedback
/// to any widget. Use this instead of manually adding Semantics + HapticFeedback
/// to every interactive element.
///
/// Example:
/// ```dart
/// AccessibilityWrapper(
///   label: 'Scan a book page. Opens the camera.',
///   haptic: HapticFeedbackType.medium,
///   onTap: _scanBookPage,
///   child: BigCircleButton(...),
/// )
/// ```
class AccessibilityWrapper extends StatelessWidget {
  /// The Semantics label for screen readers.
  final String label;

  /// Optional hint text for screen readers.
  final String? hint;

  /// Optional custom onLongPress action.
  final VoidCallback? onLongPress;

  /// The type of haptic feedback to provide on tap.
  final HapticFeedbackType haptic;

  /// Callback when the widget is tapped.
  final VoidCallback onTap;

  /// The child widget to wrap.
  final Widget child;

  const AccessibilityWrapper({
    super.key,
    required this.label,
    this.hint,
    this.onLongPress,
    this.haptic = HapticFeedbackType.medium,
    required this.onTap,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: label,
      hint: hint,
      child: GestureDetector(
        onTap: () {
          _triggerHaptic();
          onTap();
        },
        onLongPress: onLongPress != null
            ? () {
                _triggerHaptic();
                onLongPress!();
              }
            : null,
        child: child,
      ),
    );
  }

  void _triggerHaptic() {
    switch (haptic) {
      case HapticFeedbackType.light:
        HapticFeedback.lightImpact();
        break;
      case HapticFeedbackType.medium:
        HapticFeedback.mediumImpact();
        break;
      case HapticFeedbackType.heavy:
        HapticFeedback.heavyImpact();
        break;
      case HapticFeedbackType.selection:
        HapticFeedback.selectionClick();
        break;
      case HapticFeedbackType.none:
        break;
    }
  }
}

/// Types of haptic feedback available for AccessibilityWrapper.
enum HapticFeedbackType {
  /// Soft tap feedback.
  light,

  /// Standard tap feedback (default).
  medium,

  /// Strong tap feedback for important actions.
  heavy,

  /// Selection click feedback.
  selection,

  /// No haptic feedback.
  none,
}
